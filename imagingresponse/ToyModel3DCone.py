###################################################################################################
#
# ToyModel3DCone.py
#
# Copyright (C) by Shivani Kishnani, Andreas Zoglauer & contributors.
# All rights reserved.
#
# Please see the file LICENSE in the main repository for the copyright-notice. 
#  
###################################################################################################

###################################################################################################


def ToyModel3DCone(filew, layout=[10, 100, 1000], activations="relu"):

  import tensorflow as tf
  import numpy as np
  import random

  from mpl_toolkits.mplot3d import Axes3D
  import matplotlib.pyplot as plt
  from matplotlib import cm
  from matplotlib.ticker import LinearLocator, FormatStrFormatter

  import signal
  import sys
  import time
  import math
  import csv


###################################################################################################
# Step 1: Input parameters
###################################################################################################
  try:
   # First take care of Ctrl-C
    Interrupted = False
    NInterrupts = 0
    def signal_handler(signal, frame):
      print("You pressed Ctrl+C!")
      nonlocal Interrupted, NInterrupts
      Interrupted = True        
      NInterrupts += 1
      if NInterrupts >= 3:
        print("Aborting!")
        raise KeyboardInterrupt 
    signal.signal(signal.SIGINT, signal_handler)

    print("\nToyModel: (x,y) --> Compton cone for all  x, y in [-1, 1]\n")

    # x,y grid dimension
    gMinXY = -1
    gMaxXY = +1

    # x, y grid bins
    gTrainingGridXY = 30

    # z grid dimension
    gMinZ = 0
    gMaxZ = 1

    # z grid dimension - must be divisible by 4
    gTrainingGridZ = 4

    # Width of the cone
    gSigmaR = 0.1

    # Derived helper variables

    gBinSizeXY = (gMaxXY - gMinXY)/gTrainingGridXY
    gBinSizeZ = (gMaxZ - gMinZ)/gTrainingGridZ

    gGridCentersXY = np.zeros([gTrainingGridXY])
    gGridCentersZ = np.zeros([gTrainingGridZ])

    for x in range(0, gTrainingGridXY):
      gGridCentersXY[x] = gMinXY + (x+0.5)*(gMaxXY-gMinXY)/gTrainingGridXY

    for z in range(0, gTrainingGridZ):
      gGridCentersZ[z] = gMinZ + (z+0.5)*(gMaxZ-gMinZ)/gTrainingGridZ

    # Set test and traing data set parameters
    InputDataSpaceSize = 2 
    OutputDataSpaceSize = gTrainingGridXY*gTrainingGridXY*gTrainingGridZ

    SubBatchSize = 1024

    NTrainingBatches = 1
    TrainingBatchSize = NTrainingBatches*SubBatchSize

    NTestingBatches = 1
    TestBatchSize = NTestingBatches*SubBatchSize

    min_diff = 0
    max_diff = 0

    #added
    numOfTimes = 0
    model = [0, 0] #the list to return 

    TimesNoImprovement = 0
    BestMeanSquaredError = 10**30 #sys.float_info.max

  ###################################################################################################
  # Step 2: Global functions
  ###################################################################################################
 
    #added
    def file_write():
      print_l = ""
      for i in layout:
        print_l = print_l + str(i) + ","

      filew.write("Model # " + print_l[0:-2] + " with Best Mean Squared Error %d at Iteration %d.\n" % (model[0], model[1]))
      print("Wrote to file: Model # %d with Best Mean Squared Error %d at Iteration %d.\n" % (Iteration, model[0], model[1]))

    # A function for plotting 4 slices of the model in one figure
    def Plot2D(XSingle, YSingle, Title, FigureNumber = 0):
      global orig_img
      global stim_img

      XV, YV = np.meshgrid(gGridCentersXY, gGridCentersXY)
      Z = np.zeros(shape=(gTrainingGridXY, gTrainingGridXY))
      
      fig = plt.figure(FigureNumber);
      plt.subplots_adjust(hspace=0.5)

      fig.canvas.set_window_title(Title)
      for i in range(1, 5):
        
        zGridElement = int((i-1)*gTrainingGridZ/4)
      
        for x in range(gTrainingGridXY):
          for y in range(gTrainingGridXY):
            Z[x, y] = YSingle[0, x + y*gTrainingGridXY + zGridElement*gTrainingGridXY*gTrainingGridXY]
        
        ax = fig.add_subplot(2, 2, i)
        ax.set_title("Slice through z={}".format(gGridCentersZ[zGridElement]))
        contour = ax.contourf(XV, YV, Z)  

      plt.ion()
      plt.show()
      plt.pause(0.001)


    ###################################################################################################
    # Step 3: Create the training, test & verification data sets
    ###################################################################################################

    print("Info: Creating %i data sets" % (TrainingBatchSize + TestBatchSize))

    def CreateRandomResponsePoint(PosX, PosY):
      return (PosX + random.gauss(PosX, gSigma), random.uniform(gMinXY, gMaxXY))

    def get_gauss(d, sigma = 1):
      return 1/(sigma*math.sqrt(2*np.pi)) * math.exp(-0.5*pow(d/sigma, 2))

    def CreateFullResponse(PosX, PosY):
      Out = np.zeros(shape=(1, OutputDataSpaceSize))

      for x in range(0, gTrainingGridXY):
        for y in range(0, gTrainingGridXY):
          for z in range(0, gTrainingGridZ):
            r = math.sqrt((PosX - gGridCentersXY[x])**2 + (PosY - gGridCentersXY[y])**2 )
            Out[0, x + y*gTrainingGridXY + z*gTrainingGridXY*gTrainingGridXY] = get_gauss(math.fabs(r - gGridCentersZ[z]), gSigmaR);

      return Out
        
    XTrain = np.zeros(shape=(TrainingBatchSize, InputDataSpaceSize))
    YTrain = np.zeros(shape=(TrainingBatchSize, OutputDataSpaceSize))
    for i in range(0, TrainingBatchSize):
      if i > 0 and i % 128 == 0:
        print("Training set creation: {}/{}".format(i, TrainingBatchSize))
      XTrain[i,0] = random.uniform(gMinXY, gMaxXY)
      XTrain[i,1] = random.uniform(gMinXY, gMaxXY)
      YTrain[i,] = CreateFullResponse(XTrain[i,0], XTrain[i,1])     

    XTest = np.zeros(shape=(TestBatchSize, InputDataSpaceSize)) 
    YTest = np.zeros(shape=(TestBatchSize, OutputDataSpaceSize)) 
    for i in range(0, TestBatchSize):
      if i > 0 and i % 128 == 0:
        print("Testing set creation: {}/{}".format(i, TestBatchSize))
      XTest[i, 0] = random.uniform(gMinXY, gMaxXY)
      XTest[i, 1] = random.uniform(gMinXY, gMaxXY)
      YTest[i, ] = CreateFullResponse(XTest[i,0], XTest[i,1])


    ###################################################################################################
    # Step 4: Setting up the neural network
    ###################################################################################################


    print("Info: Setting up neural network...")

    # Placeholders 
    print("      ... placeholders ...")
    X = tf.placeholder(tf.float32, [None, InputDataSpaceSize], name="X")
    Y = tf.placeholder(tf.float32, [None, OutputDataSpaceSize], name="Y")


    # Layers: 1st hidden layer X1, 2nd hidden layer X2, etc.
    print("      ... hidden layers ...")

    if activations == "relu":
      activations = "tf.nn.relu6"

    for layer in layout:
      if layer == layout[0]:
        H = tf.contrib.layers.fully_connected(X, layer) #, activation_fn=eval(activations), weights_initializer=tf.truncated_normal_initializer(0.0, 0.1), biases_initializer=tf.truncated_normal_initializer(0.0, 0.1))
      else:
        H = tf.contrib.layers.fully_connected(H, layer)
   
    print("      ... output layer ...")
    Output = tf.contrib.layers.fully_connected(H, OutputDataSpaceSize, activation_fn=None)

    # Loss function 
    print("      ... loss function ...")
    #LossFunction = tf.reduce_sum(np.abs(Output - Y)/TestBatchSize)
    LossFunction = tf.reduce_sum(tf.pow(Output - Y, 2))/TestBatchSize

    # Minimizer
    print("      ... minimizer ...")
    Trainer = tf.train.AdamOptimizer().minimize(LossFunction)

    # Create and initialize the session
    print("      ... session ...")
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    print("      ... writer ...")
    writer = tf.summary.FileWriter("OUT_ToyModel3DGauss", sess.graph)
    writer.close()

    # Add ops to save and restore all the variables.
    print("      ... saver ...")
    Saver = tf.train.Saver()



    ###################################################################################################
    # Step 5: Training and evaluating the network
    ###################################################################################################


    print("Info: Training and evaluating the network")

    # Train the network
    Timing = time.process_time()

    def CheckPerformance():
      nonlocal TimesNoImprovement
      nonlocal BestMeanSquaredError

      MeanSquaredError = sess.run(tf.nn.l2_loss(Output - YTest)/TestBatchSize,  feed_dict={X: XTest})
      
      print("Iteration {} - MSE of test data: {}".format(Iteration, MeanSquaredError))

      if MeanSquaredError <= BestMeanSquaredError:    # We need equal here since later ones are usually better distributed
        BestMeanSquaredError = MeanSquaredError
        TimesNoImprovement = 0
        
        #Saver.save(sess, "model.ckpt")
        
        # Test just the first test case:
        XSingle = XTest[0:1]
        YSingle = YTest[0:1]
        print(XSingle)
        YOutSingle = sess.run(Output, feed_dict={X: XSingle})
        
        #Plot2D(XSingle, YSingle, "Original", 1)
        #Plot2D(XSingle, YOutSingle, "Reconstructed at iteration {}".format(Iteration), 2)
      else:
        TimesNoImprovement += 1

      plt.ion()
      plt.show()
      plt.pause(0.001)

      if BestMeanSquaredError == MeanSquaredError:
        return [BestMeanSquaredError, Iteration]
      else:
        return []


    # Main training and evaluation loop
    MaxIterations = 50000
    for Iteration in range(0, MaxIterations):
      # Take care of Ctrl-C
      if Interrupted == True: break

      # Train
      for Batch in range(0, NTrainingBatches):
        if Interrupted == True: break

        #if Batch%8 == 0:
        #  print("Iteration %6d, Batch %4d)" % (Iteration, Batch))

        Start = Batch * SubBatchSize
        Stop = (Batch + 1) * SubBatchSize
        sess.run(Trainer, feed_dict={X: XTrain[Start:Stop], Y: YTrain[Start:Stop]})
        
      # Check performance: Mean squared error
      if Iteration > 0 and Iteration % 10 == 0:
        new_model = CheckPerformance()
        if new_model:
          model = new_model

      if TimesNoImprovement == 100:
        print("No improvement for 30 rounds")
        break;

    YOutTest = sess.run(Output, feed_dict={X: XTest})


    Timing = time.process_time() - Timing
    if Iteration > 0: 
      print("Time per training loop: ", Timing/Iteration, " seconds")

    input("Press [enter] to EXIT")
    file_write()
    return

  except KeyboardInterrupt:
    file_write()
    return model;


    # END  
    ###################################################################################################