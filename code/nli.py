import tensorflow as tf

xavier = tf.contrib.layers.xavier_initializer

class NLI(object):
  """
  @statement is of dimensions batch_size x sentence_size x embedding_size
  """
  # batch_size x sentence_size x embedding_size
  @staticmethod
  def process_stmt_bow(statement, hidden_size, reg_list):
    with tf.name_scope("Process_Stmt_BOW"):
      # batch_size x embedding_size
      hidden = tf.reduce_mean(statement, 1)
      tf.summary.histogram("hidden", hidden)
      return hidden

  @staticmethod
  def process_stmt_LSTM_cell(hidden_size):
    with tf.name_scope("Process_Stmt_LSTM_cell"):
      return tf.nn.rnn_cell.BasicLSTMCell(hidden_size)

  """
  Run inputs through LSTM and output hidden state. Assumes that padding is with zeros.

  :param statement: Statement as a list of indices

  :return: A hidden state representing the statement

  @statement is of dimensions batch_size x sentence_size x embedding_size
  return value is of dimensions batch_size x hidden_size
  """
  @staticmethod
  def process_stmt_LSTM(statement, stmt_lens, cell, reg_list):
    with tf.name_scope("Process_Stmt_LSTM"):
      # dimensions
      batch_size = tf.shape(statement)[0]
      sen_size = tf.shape(statement)[1]

      initial_state = cell.zero_state(batch_size, tf.float32)

      # batch_size x sentence_size x hidden_size
      rnn_outputs, fin_state = tf.nn.dynamic_rnn(cell, statement,
                                              sequence_length=stmt_lens,
                                              initial_state=initial_state)
      last_rnn_output = tf.gather_nd(rnn_outputs,
                                     tf.pack([tf.range(batch_size), stmt_lens-1], axis=1))
    return last_rnn_output

  """
  Run inputs through Bi-LSTM and output concatonation of forward and backward
  final hidden state. Assumes that padding is with zeros.

  :param statement: Statement as a list of indices

  :return: A hidden state representing the statement. Concatonation of final 
  forward and backward hidden states.

  @statement is of dimensions batch_size x sentence_size x embedding_size
  return value is of dimensions batch_size x (2 x hidden_size)
  """
  @staticmethod
  def process_stmt_BiLSTM(statement, stmt_lens, cell_fw, cell_bw, reg_list):
    with tf.name_scope("Process_Stmt_Bi-LSTM"):
      # dimensions
      batch_size = tf.shape(statement)[0]
      sen_size = tf.shape(statement)[1]

      initial_state_fw = cell_fw.zero_state(batch_size, tf.float32)
      initial_state_bw = cell_bw.zero_state(batch_size, tf.float32)

      rnn_outputs, fin_state = tf.nn.bidirectional_dynamic_rnn(cell_fw, cell_bw, statement,
                                              sequence_length=stmt_lens,
                                              initial_state_fw=initial_state_fw,
                                              initial_state_bw=initial_state_bw)
      rnn_outputs = tf.concat(2, rnn_outputs)
      last_rnn_output = tf.gather_nd(rnn_outputs,
                                     tf.pack([tf.range(batch_size), stmt_lens-1], axis=1))
    return last_rnn_output

  @staticmethod
  def merge_processed_stmts(stmt1, stmt2, hidden_size, reg_list):
    stmt1_size = stmt1.get_shape().as_list()[1]
    stmt2_size = stmt2.get_shape().as_list()[1]

    # weight hidden layers before merging
    with tf.variable_scope("Hidden-Weights"):

      W1 = tf.get_variable("W1", shape=(stmt1_size, hidden_size), initializer=xavier())
      r1 = tf.matmul(stmt1, W1)
      tf.summary.histogram("r1", r1)

      W2 = tf.get_variable("W2", shape=(stmt2_size, hidden_size), initializer=xavier())
      r2 = tf.matmul(stmt2, W2)
      tf.summary.histogram("r2", r2)

    return tf.concat(1, [r1, r2], name="merged")

  @staticmethod
  def feed_forward(merged, dropout_ph, hidden_size, num_classes, reg_list):
    with tf.variable_scope("FF"):
      # r1 = tanh(merged W1 + b1)
      with tf.variable_scope("FF-First-Layer"):
        merged_size = merged.get_shape().as_list()[1]
        W1 = tf.get_variable("W", shape=(merged_size, hidden_size), initializer=xavier())
        b1 = tf.Variable(tf.zeros([hidden_size,]), name="b")
        r1 = tf.nn.relu(tf.matmul(merged, W1) + b1, name="r")
        r1_dropout = tf.nn.dropout(r1, dropout_ph)

        tf.summary.histogram("W", W1)
        tf.summary.histogram("b", b1)
        tf.summary.histogram("r1", r1)

      # r2 = tanh(r1 W2 + b2)
      with tf.variable_scope("FF-Second-Layer"):
        W2 = tf.get_variable("W", shape=(hidden_size, hidden_size), initializer=xavier())
        b2 = tf.Variable(tf.zeros([hidden_size,]), name="b")
        r2 = tf.nn.relu(tf.matmul(r1_dropout, W2) + b2, name="r")
        r2_dropout = tf.nn.dropout(r2, dropout_ph)

        tf.summary.histogram("W", W2)
        tf.summary.histogram("b", b2)
        tf.summary.histogram("r2", r2)

      # r3 = tanh(r2 W3 + b3)
      with tf.variable_scope("FF-Third-Layer"):
        W3 = tf.get_variable("W", shape=(hidden_size, num_classes), initializer=xavier())
        b3 = tf.Variable(tf.zeros([num_classes,]), name="b")
        r3 = tf.nn.relu(tf.matmul(r2_dropout, W3) + b3, name="r")
        preds = r3

        tf.summary.histogram("W", W3)
        tf.summary.histogram("b", b3)
        tf.summary.histogram("preds", preds)

      reg_list.extend((W1, W2, W3))
      return preds
