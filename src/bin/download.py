import os
import sys

# , ""
required_bin = ["bedGraphToBigWig"]

for b in required_bin:
    durl = "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/" + b
    cmd = "wget %s -P ./linux/" % durl
    os.system(cmd)


for b in required_bin:
    durl = "https://hgdownload.soe.ucsc.edu/admin/exe/macOSX.arm64/" + b
    cmd = "wget %s -P ./macarm" % durl
    os.system(cmd)



