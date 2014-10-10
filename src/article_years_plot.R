library(ggplot2)

all_vec <- read.csv('article_years.csv')[,2]
clin_vec <- read.csv('clinical_article_years.csv')[,2]
non_clin_vec <- read.csv('non_clinical_article_years.csv')[,2]

all_df <- data.frame(year = all_vec)
all_df$type = 'all'
clin_df <- data.frame(year = clin_vec)
clin_df$type = 'clin'
non_clin_df <- data.frame(year = non_clin_vec)
non_clin_df$type = 'non_clin'

agg_df <- rbind(all_df, clin_df, non_clin_df)
means_df <- data.frame(type = c('all', 'clin', 'non_clin'), val = c(mean(all_vec, na.rm = TRUE), mean(clin_vec, na.rm = TRUE), mean(non_clin_vec, na.rm = TRUE)))

range_lo <- quantile(agg_df$year, 0.05, na.rm = TRUE)
range_hi <- max(agg_df$year, na.rm = TRUE)

ggplot(agg_df, aes(x = year, colour = type)) +
  geom_density() +
  geom_vline(data = means_df, aes(xintercept = val, colour = type), linetype = 'dashed', size = 1) +
  scale_x_continuous(limits = c(range_lo, range_hi + 5), breaks = round(seq(range_lo, range_hi  + 5, by = 5),1))
ggsave('article-years.pdf', width=18, height=8)
