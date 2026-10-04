PANDOC ?= pandoc
OUT := build

$(OUT)/index.html: article.md site/template.html site/site.css $(wildcard images/*)
	mkdir -p $(OUT)
	cp site/site.css $(OUT)/
	rsync -a images $(OUT)/
	$(PANDOC) article.md -o $@ --standalone \
	  --template=site/template.html --mathjax \
	  --syntax-highlighting=pygments

.PHONY: clean
clean:
	rm -rf $(OUT)
