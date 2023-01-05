
import os
import re
import sys


def fasta_reader(input_path):
    res = {}

    contig = ""
    seq = ""
    with open(input_path) as f:
        for l in f:
            l = l.strip()
            if l.startswith(">"):
                if seq != "":
                    res[contig] = seq
                    seq = ""

                contig = l[1:]
                continue

            seq += l.upper()

    res[contig] = seq

    return res




def cov2methylC(input_path, output_path, genome_path=None):

    f1 = open(input_path)
    f2 = open(output_path, "w")

    genome = {}
    if genome_path and os.path.exists(genome_path):
        genome = fasta_reader(genome_path)

    for l in f1:
        l = l.strip().split("\t")

        chromosome = l[0]
        start = int(l[1])
        end = int(l[2])
        if start == end:
            start -= 1

        strand = "+"
        if chromosome in genome:
            seq = genome[chromosome]
            if seq[start] == "G":
                strand = "-"

        m_count = int(l[4])
        nom_count = int(l[5])
        mlevel = m_count / (m_count + nom_count)

        newe = [chromosome, start, end, "CG", round(mlevel, 3), strand, m_count + nom_count]
        newl = "\t".join(list(map(str, newe))) + "\n"
        f2.write(newl)

    return



if __name__ == "__main__":
    pass

    cov2methylC("./test/test.cov", "x.methylc", genome_path="./genome/hg38.fasta")




