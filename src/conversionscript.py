import os
import sys




def cov2methylC(input_path, output_path):

    f1 = open(input_path)
    f2 = open(output_path, "w")
    for l in f1:
        l = l.strip().split("\t")


        start = int(l[1])
        end = int(l[2])
        if start == end:
            start -= 1

        m_count = int(l[4])
        nom_count = int(l[5])
        mlevel = m_count / (m_count + nom_count)

        newe = [l[0], start, end, "CG", round(mlevel, 3), "+", m_count + nom_count]
        newl = "\t".join(list(map(str, newe))) + "\n"
        f2.write(newl)
    return



if __name__ == "__main__":

    cov2methylC("test.cov", "test.cov.methylc")



