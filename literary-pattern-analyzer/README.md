# Literary Pattern Analyzer
*Skills: Python, Natural language Processing, Visualization*

### Overview
This program consists of tools for use in identifying structural patterns in text:
1. Custom Lexical Dispersion plot (by text segment)
2. Word Intentionality Plot, which plots the probability that the density of a word within a text segment is not random
3. Parallelism Arc Plot, which shows the strength of parallelism between text segments
4. Topic Plot, which uses Latent Dirichlet Allocation to show changes in topic within a text

### Motivation
Today when many read literature, they primarily focus on semantic meaning or the more familiar semantic literary devices such as similes, metaphor, hyperbole, personification etc. However, ancient texts often contain structural devices such as repetition and parallism which are more difficult for today's readers to recognize (possibly because these devices require a stronger long term memory that is associated with the distant past when oral tradition was more dominant). The tools in this program can be used to help detect intentional or rhetorical repetition, identify changes in topic or emphasis, and identify literary devices such as lists of textual units with similar structure, and pairs of parallel or anti-parallel (chiastic) sequences of textual units, which are commonly used in ancient texts.

### Pre-processing
Before analysis, pre-processing is performed, which includes tokenization and splitting the text into segments. A segment can be a verse, a line, or a sentence, and may also be hierarchically defined as chapter:verse, stanza:line, or paragraph:sentence. If the text is saved locally in a .txt file, it can be pre-processed using the function localtext(filepath, split). 

Specify how to split the text into segments using the split argument. If the text already has verse numbers, the split argument should be a regex expression that uniquely identifies the verse numbers, such as '\d+:?:d*' or '\d+ +'. If there are no verse numbers, the split argument can be set to 'sentence', which will split the text by sentence, or the argument can be an integer, which will split the text by number of tokens.  If the text is split by sentence or number of tokens, a Python prompt for the output file path will appear. This file is a copy of the text with the verse numbers inserted.

It may be desirable to split a text in other ways than those mentioned above. Or in some cases where verse numbers and numbers within the text cannot be distinguished using regex, using tags in an html or xml version of the text (rather than .txt) may be preferred. In these cases the user should write a script for scraping and splitting the text and generate the appropriate global variables as follows. The global variable name 'book' must be assigned to the list of tokens in the text (use nltk for to generate the list).

Then a list of pairs (either lists or tuples with 2 elements) of starting word number (index of the token list) and segment identifier must be generated. The global variable name 'verselist' must be assigned to this list. For example: \[(0,'1:1'),(32,'1:2'),(48,'1:3'),(60,'1:4'),(84,'1:5')\].

As examples, the scraping and pre-processing procedure is built into this application for Homer's Iliad and biblical books, primarily due the the relatively straightforward structure of their websites.


