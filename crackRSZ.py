#mod by strum

import sys
import random
from sage.all_cmdline import *   
from bitcoin import *

order = int(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
filename='file.txt'
B = 255
limit = 10000
address = sys.argv[1]
def extended_gcd(aa, bb):
    lastremainder, remainder = abs(aa), abs(bb)
    x, lastx, y, lasty = 0, 1, 1, 0
    while remainder:
        lastremainder, (quotient, remainder) = remainder, divmod(lastremainder, remainder)
        x, lastx = lastx - quotient*x, x
        y, lasty = lasty - quotient*y, y
    return lastremainder, lastx * (-1 if aa < 0 else 1), lasty * (-1 if bb < 0 else 1)

def modular_inv(a, m):
    g, x, y = extended_gcd(a, m)
    if g != 1:
        raise ValueError
    return x % m

def load_csv(filename):
  msgs = []
  sigs = []
  pubs = []
  fp = open(filename)
  n=0
  for line in fp:
    if n < limit:
      l = line.rstrip().split(",")
      #sys.stderr.write(str(l)+"\n")
      R,S,Z = l
      msgs.append(int(Z,16))
      sigs.append((int(R,16),int(S,16)))
      #pubs.append(pub)
      n+=1
  return msgs,sigs

msgs,sigs = load_csv(filename)

msgn, rn, sn = [msgs[-1], sigs[-1][0], sigs[-1][1]]
rnsn_inv = rn * modular_inv(sn, order)
mnsn_inv = msgn * modular_inv(sn, order)
m = len(msgs)
sys.stderr.write("Using: %d total sigs...\n" % m)
def make_matrix(msgs,sigs,c):
  m = len(msgs)
  sys.stderr.write("Using: %d sigs...\n" % 20)
  matrix = Matrix(QQ,m+2, m+2)

  for i in range(0+c,20+c):
    #matrix.append([0] * i + [order] + [0] * (m-i+1))
    matrix[i,i] = order

  #print(matrix)

  for i in range(0,m):
    x0=(sigs[i][0] * modular_inv(sigs[i][1], order)) - rnsn_inv
    x1=(msgs[i] * modular_inv(sigs[i][1], order)) - mnsn_inv
    #print(m,i,x0,x1)
    matrix[m+0,i] = x0
    matrix[m+1,i] = x1

  #print("m",m)
  #print("i",i)
 
  matrix[m+0,i+1] = (int(2**B) / order)
  matrix[m+0,i+2] = 0
  matrix[m+1,i+1] = 0
  matrix[m+1,i+2] = 2**B

  return matrix
  
keys=[]
def try_red_matrix(m):
  for row in m:
    potential_nonce_diff = row[0]
    #print (potential_nonce_diff)
    # Secret key = (rns1 - r1sn)-1 (snm1 - s1mn - s1sn(k1 - kn))
    potential_priv_key = (sn * msgs[0]) - (sigs[0][1] * msgn) - (sigs[0][1] * sn * potential_nonce_diff)
    try:
      potential_priv_key *= modular_inv((rn * sigs[0][1]) - (sigs[0][0] * sn), order)

      key = potential_priv_key % order
      if key not in keys:
        keys.append(key)

    except Exception as e:
      sys.stderr.write(str(e)+"\n")
      pass

def display_keys(keys):
  for key in keys:
    v = "%064x" % key
    myhex = v[:64]
    priv = myhex
    pub = privtopub(priv)
    priv = myhex
    pub = encode_pubkey(privtopub(priv), "bin_compressed")
    print(priv)
    if pubtoaddr(pub) == address:
        print("UWIN",priv)
  
c = 0
while m > 20+c:
  matrix = make_matrix(msgs,sigs,c)
  new_matrix = matrix.LLL(early_red=True, use_siegel=True)
  try_red_matrix(new_matrix)
  display_keys(keys)
  c+=20
