#!/usr/bin/env Rscript

library(readr)
library(treemap)

# Read command arguments
args = commandArgs(trailingOnly=TRUE)

# Read data from stdin
data = read_delim(stdin(), ' ', col_names=c('bytes', 'package'))

png(filename=args[1], width=1200, height=1200)
treemap(data, index="package", vSize="bytes", type="index", fontsize.labels=20)
dev.off()
