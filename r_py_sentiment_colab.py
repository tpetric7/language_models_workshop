# -*- coding: utf-8 -*-
"""R_Py_sentiment_Colab.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/tpetric7/language_models_workshop/blob/main/R_Py_sentiment_Colab.ipynb

# Ocena razpoloženja (sentimenta)

Sentimentno analizo bomo opravili v računalniškem jeziku R, vendar ob podpori modela s transformersko arhitekturo, ki ga prikličemo iz Pythonovega okolja.

## Priprava Pythonovega virtualnega okolja

V virtualnem operacijskem sistemu Linux Googlovega kolaboratorija je treba najprej pripraviti Pythonovo virtualno okolje in namestiti Pythonove module, na katere se lahko sklicujejo funkcije v računalniškem jeziku R.

V nevirtualnih operacijskih sistemih je priprava preprostejša.
"""

# If needed, run shell commands in R via system()
system("which python")
system("python --version")
system("sudo apt-get update -y")
system("sudo apt-get install -y python3-dev")
system("sudo apt-get install -y python3-venv")

"""## R knjižnica reticulate

Knjižnica reticulate je vmesnik za delo s Pythonom. Knjižnico namestimo z ukazom install.packages(), ki je značilen za R-ovo sinttakso. Prikličemo jo pa s funkcijo library().
"""

install.packages("reticulate")
library(reticulate)

"""## Ustvarjanje Pythonovega okolja za R"""

# virtualenv_create("bertopic", python = "/usr/local/bin/python")
system("python3 -m venv /root/.virtualenvs/bertopic")

system("pip install virtualenv")
system("virtualenv /root/.virtualenvs/bertopic")

"""## Namestitev Pythonovih knjižnic

Najprej s funkcijo use_virtualenv() aktiviramo zgoraj pripravljeno Pythonovo okolje "bertopic". Potem s py_install() nameščamo vse potrebne Pythonove knjižnice (module).
"""

library(reticulate)
use_virtualenv("bertopic", required = TRUE)
py_install("pandas", envname = "bertopic")
py_install(c("numpy", "matplotlib"), envname = "bertopic")
py_install("transformers", envname = "bertopic")
py_install("python-docx", envname = "bertopic")

system("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
system("pip install transformers")
system("pip install sentencepiece")
system("pip install protobuf")

"""## Priklic Pythonovih knjižnic"""

# Import necessary Python modules
# Inicializacija knjižnic
re <- import("re")
datetime <- import("datetime")
docx <- import("docx")
Document <- docx$Document
pd <- import("pandas")
np <- import("numpy")
transformers <- import("transformers")
pipeline <- transformers$pipeline

"""## Namestitev knjižnic R"""

install.packages(c("tidyverse", "tidytext"))

"""## Priklic knjižnic R"""

library(tidyverse)
library(tidytext)

"""## Branje besedila"""

input_folder <- "/content/"
input_file <- "Sporocilo sodelavcem univerze o kibernapadu.txt"
text <- read_lines(file.path(input_folder, input_file), locale = locale(encoding = 'UTF-8'))
cat(head(text, 5), sep = "\n")

"""## Branje nezaželenih besed

Če potrebno, bomo izločili funkcijske besede, ki ne prispevajo k tematiki.
"""

input_folder <- "/content/"
input_file <- "all_stopwords.txt"
all_stopwords <- read_lines(file.path(input_folder, input_file))

"""## Razdelitev na povedi

Naš model najbolje deluje s povedmi. Zato razdelimo besedilo na povedi, bistveno merilo za segmentacijo pa so končna ločila.
"""

txt <- tibble(text = text)
sents <- txt %>%
  unnest_sentences(sentences, text, to_lower = FALSE)
sentences <- str_squish(sents$sentences)
head(sentences)

"""## Priklic modela za sentimentno analizo"""

# Naloži model sentimentne analize
sentiment_analysis <- pipeline('sentiment-analysis', model = 'cardiffnlp/twitter-xlm-roberta-base-sentiment')

"""## Analiza razpoloženja (sentimenta)"""

# Analiziraj sentiment
results <- lapply(sentences, function(sentence) {
  # sentiment <- py_to_r(sentiment_analysis(sentence))[[1]]
  sentiment <- sentiment_analysis(sentence)[[1]]
  list(sentence = sentence, label = sentiment$label, score = sentiment$score)
})

head(results)

"""## Pretvorba v podatkovni niz"""

# Convert results to a data.frame
results_df <- do.call(rbind, lapply(results, as.data.frame))
rownames(results_df) <- NULL  # Remove row names
head(results_df)

write.csv(results_df, file = "results.csv", row.names = FALSE)

"""## Dodeljevanje barv"""

# Map sentiment labels to colors
get_color <- function(label) {
  if (label == "POSITIVE") {
    return("green")
  } else if (label == "NEGATIVE") {
    return("red")
  } else {
    return("gray")
  }
}

"""## Predloga spletne strani"""

# Ustvari HTML vsebino
html_content <- "<!DOCTYPE html>
<html>
<head>
    <title>Sentiment Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.8; margin: 20px; }
        .positive { color: green; }
        .neutral { color: gray; }
        .negative { color: red; }
    </style>
</head>
<body>
<h1>Sentiment Analysis Results</h1>
<p>Below are the sentences from the document, colored based on their sentiment:</p>
"

"""## Dodeljevanje povedi barvam"""

# Dodaj povedi v HTML vsebino
for (result in results) {
  color_class <- tolower(result$label)
  html_content <- paste0(html_content, "<p class='", color_class, "'>", result$sentence, "</p>\n")
}

# Zaključi HTML vsebino
html_content <- paste0(html_content, "</body></html>")

"""## Shrani HTML datoteko"""

# Shrani HTML datoteko
output_file <- "sentiment_analysis_colored.html"
writeLines(html_content, output_file)

cat("HTML file saved as", output_file, ". Open it in a browser to view the results.\n")