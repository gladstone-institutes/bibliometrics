library(moments)

args <- commandArgs(trailingOnly = TRUE)
input_path <- args[1]
input_file <- file(input_path, open = 'r')

all_counts <- list()

while (TRUE) {
  line <- readLines(input_file, n = 1, warn = FALSE)
  if (length(line) <= 0) {
    break
  }
  author_name <- line
  line <- readLines(input_file, n = 1, warn = FALSE)
  counts <- unlist(lapply(strsplit(line, ' '), as.numeric))

  all_counts[[author_name]] <- counts
}

close(input_file)

max_count <- 0
max_freq <- 0

for (author_name in names(all_counts)) {
  if (author_name == 'collins fs' || author_name == 'rommens jm') {
    next
  }
  counts <- all_counts[[author_name]]
  counts_hist <- hist(counts, plot=FALSE)

  max_count <- max(max_count, tail(counts_hist$mids, n=1))
  max_freq <- max(max_freq, max(counts_hist$counts))
}


for (author_name in names(all_counts)) {
  counts <- all_counts[[author_name]]

  #hist(counts, main = author_name, xlim = range(0, max_count), ylim = range(0, max_freq), breaks = 5)
  hist(counts, main = author_name)
  coords <- par('usr')
  text(coords[2], coords[4], adj = c(1,1),
       sprintf('mean: %6.2f\nsd: %6.2f\nskew: %6.2f\nkurt: %6.2f',
               mean(counts), sd(counts), skewness(counts), kurtosis(counts)))
}
