import numpy as np

dm = np.zeros((80,10)) # make a data matrix
for i in range(10):                             
	j = i*8; dm[j:j+8,i] = 1 # fill matrix with 1s (group average)
np.savetxt('datamatrix.txt',dm,delimiter='\t',fmt='%d')
