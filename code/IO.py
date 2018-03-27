# a little function collection to read and write test files and manipulate 
# to prettier python formats
import os
def str2list(string_line):
    '''
    takes a string as input and parses it into its pieces (separated by space I think)
    saving it into a list. Also, tries to convert datatype to float/int if possible
    '''
    l = []
    s = string_line.split()
    for v in s:
        try:
            l.append(int(v))
        except:
            try:
                l.append(float(v))
            except:    
                l.append(v)
    return l


def write2CSV(f,alist):
    ''' 
    Writes values in a list into specified file with commas as separators
    ''' 
    for ind,value in enumerate(alist):
        if ind == len(alist)-1:
            f.write(str(value))
        else:
            f.write(str(value)+',')
    f.write('\n')

def makeDirs(*args):
    """
    Creates a directory if it doesnt exist yet. 
    Input are strings defining the paths
    """
    for arg in args:
        if not os.path.exists(arg):
              os.makedirs(arg)   