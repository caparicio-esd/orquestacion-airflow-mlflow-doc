# Makefile para compilar el Manual Técnico de Apache Airflow y MLflow
TECTONIC ?= $(shell command -v tectonic 2>/dev/null || echo $(HOME)/.local/bin/tectonic)
PDF_NAME = orquestacion-airflow-mlflow-manual.pdf

.PHONY: all clean check

all: $(PDF_NAME)

$(PDF_NAME): main.tex preamble.tex chapters/*.tex
	$(TECTONIC) -X compile main.tex --keep-logs
	cp main.pdf $(PDF_NAME)

check: $(PDF_NAME)
	@pdfinfo $(PDF_NAME) | grep -E 'Title|Pages|Page size'

clean:
	rm -f main.pdf main.log main.aux main.toc main.lof main.lot main.lol main.out $(PDF_NAME)
