import os
import sys


f = open("/etc/ssl/openssl.cnf")
lines = [i for i in f]
f.close()

for i,l in enumerate(lines):

    if l == "MinProtocol = TLSv1.2\n":
        lines[i] = "MinProtocol = TLSv1.0\n"

    if i == 361 and l == "CipherString = DEFAULT@SECLEVEL=2\n":
        pass
        #lines[i] = "\n"


f = open("/etc/ssl/openssl.cnf", "w")
for i in lines:
    pass
    f.write(i)
f.close()


f = open(".gtccred", "w")
f.write("fake@gmail.com xxxx")
f.close()





