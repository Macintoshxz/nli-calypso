from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time
import logging

import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
from tensorflow.python.ops import variable_scope as vs

# from evaluate import exact_match_score, f1_score

logging.basicConfig(level=logging.INFO)

def get_optimizer(opt):
  if opt == "adam":
    optfn = tf.train.AdamOptimizer
  elif opt == "sgd":
    optfn = tf.train.GradientDescentOptimizer
  else:
    assert (False)
  return optfn

"""
Represent "Premise" LSTM portion of model.
"""
class Premise(object):
  def __init__(self, hidden_size):
    self.cell = tf.contrib.rnn.BasicLSTMCell(hidden_size)

  """
  Run inputs through LSTM and output hidden state.

  :param inputs: Inputs as embeddings

  :return: A hidden state representing the premise

  @inputs is of dimensions sentence_size x batch_size x embedding_size
  return value is of dimensions batch_size x hidden_size
  """
  def process(self, inputs):
    batch_size = tf.shape(inputs)[1]
    initial_state = self.cell.zero_state(batch_size, tf.float32)

    output, state = tf.nn.dynamic_rnn(cell, inputs, initial_state=initial_state, time_major=True)

    return state[-1]

# For now, hypothesis is identical to premise
Hypothesis = Premise

class NLISystem(object):
  def __init__(self, premise, hypothesis, *args):

    vocab_size, embedding_size, num_classes = args

    # ==== set up placeholder tokens ========
    # Premise and Hypothesis should be input as matrix of sentence_len x batch_size x embedding_size
    self.premise_placeholder = tf.placeholder(tf.float32, shape=(None, None, embedding_size))
    self.hypothesis_placeholder = tf.placeholder(tf.float32, shape=(None, None, embedding_size))
    self.embedding_placeholder = tf.placeholder(tf.float32, shape=(vocab_size, embedding_size))

    # Output labels should be a matrix of batch_size x num_classes
    self.output_placeholder = tf.placeholder(tf.float32, shape=(None, num_classes))

    # ==== assemble pieces ====
    with tf.variable_scope("nli", initializer=tf.uniform_unit_scaling_initializer(1.0)):
      hp = premise.process(premise_placeholder)
      hh = hypothesis.process(hypothesis_placeholder)

      merged = tf.concat([hp, hh], 1)
      
      # r = ReLU(merged W1 + b1)
      hidden_size = tf.shape(merged)[1]
      W1 = tf.get_variable("W1", shape=(hidden_size, Config.hidden_size), initializer=tf.contrib.layers.xavier_initializer())
      b1 = tf.get_variable("b1", shape=(Config.hidden_size,), initializer=tf.contrib.layers.xavier_initializer())
      r = tf.nn.relu(tf.matmul(merged, w1) + b1)
      
      # softmax(rW2 + b2)
      W2 = tf.get_variable("W2", shape=(Config.hidden_size, Config.num_classes), initializer=tf.contrib.layers.xavier_initializer())
      b2 = tf.get_variable("b2", shape=(Config.num_classes,), initializer=tf.contrib.layers.xavier_initializer())

      # prediction before softmax layer
      self.preds = tf.matmul(r, W2) + b2

  def add_train_op(self):
    loss = tf.nn.softmax_cross_entropy_with_logits(self.preds, output_placeholder)
    self.train_op = get_optimizer().minimize(loss)
    
  #############################
  # TRAINING
  #############################

  def optimize(self, session, embeddings, train_premise, train_hypothesis, train_y):
    input_feed = {
      self.premise_placeholder: train_premise,
      self.hypothesis_placeholder: train_hypothesis,
      self.embedding_placeholder: embeddings,
      self.output_placeholder: train_y
    }

    output_feed = [self.train_op]
    outputs = session.run(output_feed, input_feed)

    return outputs

  """
  Loop through dataset and call optimize() to train model

  :param session: passed in from train.py
  :param dataset: a representation of data
  :param train_dir: path to the directory where the model checkpoint is saved

  """
  def train(self, session, dataset, train_dir, embeddings, batch_size):
    tic = time.time()
    params = tf.trainable_variables()
    num_params = sum(map(lambda t: np.prod(tf.shape(t.value()).eval()), params))
    toc = time.time()
    logging.info("Number of params: %d (retreival took %f secs)" % (num_params, toc - tic))

    for i, batch in enumerate(minibatches(dataset, batch_size)):
      optimize(session, embeddings, *batch)

  #############################
  # VALIDATION
  #############################

  def test(self, session, valid_x, valid_y):
    input_feed = {}

    # fill in this feed_dictionary like:
    # input_feed['valid_x'] = valid_x

    output_feed = [self.preds]

    outputs = session.run(output_feed, input_feed)

    return outputs

  def validate(self, sess, valid_dataset):
    """
      Iterate through the validation dataset and determine what
      the validation cost is.

      This method calls self.test() which explicitly calculates validation cost.

      How you implement this function is dependent on how you design
      your data iteration function

      :return:
      """
    valid_cost = 0

    for valid_x, valid_y in valid_dataset:
      valid_cost = self.test(sess, valid_x, valid_y)

    return valid_cost

  #############################
  # TEST
  #############################

  # def decode(self, session, test_x):
  #   input_feed = {}

  #   # fill in this feed_dictionary like:
  #   # input_feed['test_x'] = test_x

  #   output_feed = []

  #   outputs = session.run(output_feed, input_feed)

  #   return outputs

  def predict(self, session, test_x):

    yp, yp2 = self.decode(session, test_x)

    a_s = np.argmax(yp, axis=1)
    a_e = np.argmax(yp2, axis=1)

    return (a_s, a_e)

  def evaluate
_prediction(self, session, dataset, sample=100, log=False):
    f1 = 0.
    em = 0.

    if log:
      logging.info("F1: {}, EM: {}, for {} samples".format(f1, em, sample))

    return f1, em

