# -*- coding: utf-8 -*-
"""
@author: strum
"""

from bitcoin import *
import collections
import hashlib
import os
import sys
import argparse
from urllib.request import urlopen

print('Enter your address:')
address = input()
print('Enter number of txos to search for:')#enter number of txos out from address
k = input()
k = int(k)
#==============================================================================
N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141

def getraw(txid):
    try:
        htmlfile = urlopen("https://blockchain.info/rawtx/%s?format=hex" % txid, timeout = 60)
    except:
        print('Unable to connect internet to fetch RawTx. Exiting..')
        sys.exit(1)
    else: res = htmlfile.read().decode('utf-8')
    return res

def get_rs(sig):
    rlen = int(sig[2:4], 16)
    r = sig[4:4+rlen*2]
#    slen = int(sig[6+rlen*2:8+rlen*2], 16)
    s = sig[8+rlen*2:]
    return r, s
    
def split_sig_pieces(script):
    sigLen = int(script[2:4], 16)
    sig = script[2+2:2+sigLen*2]
    r, s = get_rs(sig[4:])
    pubLen = int(script[4+sigLen*2:4+sigLen*2+2], 16)
    pu = script[4+sigLen*2+2:]
    return r, s, pu

def extended_gcd(aa, bb):
    lastremainder, remainder = abs(aa), abs(bb)
    x, lastx, y, lasty = 0, 1, 1, 0
    while remainder:
        lastremainder, (quotient, remainder) = remainder, divmod(lastremainder, remainder)
        x, lastx = lastx - quotient*x, x
        y, lasty = lasty - quotient*y, y
    return lastremainder, lastx * (-1 if aa < 0 else 1), lasty * (-1 if bb < 0 else 1)

def modinv(a, m):
    g, x, y = extended_gcd(a, m)
    if g != 1:
        raise ValueError
    return x % m

# Returns list of this list [first, sig, pub, rest] for each input
def parseTx(txn):
    if len(txn) < 130:
        print('[WARNING] rawtx most likely incorrect. Please check..')
        sys.exit(1)
    inp_list = []
    ver = txn[:8]
    inp_nu = int(txn[8:10], 16)
    
    first = txn[0:10]
    cur = 10
    for m in range(inp_nu):
        prv_out = txn[cur:cur+64]
        var0 = txn[cur+64:cur+64+8]
        cur = cur+64+8
        scriptLen = int(txn[cur:cur+2], 16)
        script = txn[cur:2+cur+2*scriptLen] #8b included
        r, s, pubb = split_sig_pieces(script)
        seq = txn[2+cur+2*scriptLen:10+cur+2*scriptLen]
        if pubtoaddr(pubb) == address:
            inp_list.append([prv_out, var0, r, s, pubb, seq])
            cur = 10+cur+2*scriptLen
        else:
            return False
    rest = txn[cur:]
    return [first, inp_list, rest]

# =============================================================================
def h(n):
  return hex(n).replace("0x","").zfill(64)

def write(r,s,z):
    with open('file.txt', 'a') as out:
        out.write(h(r)+","+h(s)+","+h(z)+'\n')

def getrsz(parsed):
    res = []
    first, inp_list, rest = parsed
    tot = len(inp_list)
    for one in range(tot):
        e = first
        for i in range(tot):
            e += inp_list[i][0] # prev_txid
            e += inp_list[i][1] # var0
            if one == i: 
                e += '1976a914' + HASH160(inp_list[one][4]) + '88ac'
            else:
                e += '00'
            e += inp_list[i][5] # seq
        e += rest + "01000000"
        z = hashlib.sha256(hashlib.sha256(bytes.fromhex(e)).digest()).hexdigest()
        z1 = (int(z, 16))
        r = (int(inp_list[one][2],16))
        s = (int(inp_list[one][3],16))
        sigs = write(r,s,z1)

def load(file):
    signatures=[]
    import csv
    with open(file,'r') as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=",")
        line = 0
        for row in csv_reader:
            r=int(row[0],16)
            s=int(row[1],16)
            z=int(row[2],16)
            t=tuple([r,s,z])
            signatures.append(t)
            line+=1
    return signatures

def lord(file):
    signatures=[]
    import csv
    with open(file,'r') as csv_file:
        csv_reader = csv.reader(csv_file,delimiter=",")
        line = 0
        for row in csv_reader:
            r=int(row[0],16)
            s=int(row[1],16)
            z=int(row[2],16)
            t=tuple([r,s,z])
            signatures.append(t)
            line+=1
    return len(signatures)

def scan(addr):
	urladdr = 'https://blockchain.info/address/%s?format=json&offset=%s'
	addrdata = json.load(urlopen(urladdr % (addr, '0')))
	ntx = addrdata['n_tx']
	print("This address has",ntx,"transactions")
	txs = []
	if ntx > 10000:
		ntx = 9999
	for i in range(0, ntx//50 + 1):
		sys.stderr.write("Fetching Txs from offset\t%s\n" % str(i*50))
		jdata = json.load(urlopen(urladdr % (addr, str(i*50))))
		txs.extend(jdata['txs'])
	addrdata['txs'] = txs
	inputs = []
	y = 0	
	z = 0
	while z < k:
		inputs.append(addrdata['txs'][y]['hash'])
		txid = addrdata['txs'][y]['hash']
		tx = getraw(txid)		
		if parseTx(tx) != False:
			rs = parseTx(tx)
			getrsz(rs)
			y+=1
			z+=1
		else:
			y+=1
#==============================================================================
def HASH160(pubk_hex):
    return hashlib.new('ripemd160', hashlib.sha256(bytes.fromhex(pubk_hex)).digest() ).hexdigest()
#==============================================================================

open("file.txt", "a")
scan(address)
