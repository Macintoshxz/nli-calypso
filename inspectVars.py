import cPickle as pickle
import numpy as np

# indexes = []
names = ['context', 'states', 'states-context', 'tf.mul(states, context)']
# with open("ff_vars") as f:
#   for i, name in enumerate(names):
#     var = pickle.load(f)
#     print("P " + names[i] + ': ' + len(np.argwhere(np.isnan(var))) + " out of "  + var.shape())

#   for i, name in enumerate(names):
#     var = pickle.load(f)
#     print("H " + names[i] + ': ' + len(np.argwhere(np.isnan(var))) + " out of " + var.shape())

with open("mvars") as f:
  variables = []
  for _ in xrange(len(names) * 2):
    variables.append(pickle.load(f))
  print("Variables loaded!")

  while True:
    P_H = raw_input("P or H? ")
    name = raw_input("What variable would you like to inspect: ")
    if name == '':
      break

    var_idx = names.index(name)
    if P_H == "H":
      var_idx += len(names)

    while True:
      indexTup = raw_input("Index: ")
      if indexTup == '':
        break
      x, y = indexTup.strip().split(',')

      print("Value: " + str(variables[var_idx][int(x), int(y)]))

# f = open("ff_vars", "w")

# for _ in xrange(len(names) * 2):
#   pickle.dump(np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]]), f)

# f.close()





