# Literary Pattern Analyzer
*Skills: Python, Natural language Processing, Visualization*

### Overview
This program consists of tools for use in identifying structural patterns in text:
1. Custom Lexical Dispersion plot (by text segment)
2. Word Intentionality Plot, which plots the probability that the density of a word within a text segment is not random
3. Parallelism Arc Plot, which shows the strength of parallelism between text segments
4. Topic Plot, which uses Latent Dirichlet Allocation to show changes in topic within a text
These tools can be used to help detect intentional or rhetorical repetition, identify changes in topic or emphasis,
and identify literary devices such as lists of textual units with similar structure, pairs of parallel or anti-parallel
(chiastic) sequences of textual units, which are commonly used in ancient texts.

The text requires pre-processing, which includes tokenization and splitting the text into segments.
A segment can be a verse, a line, or a sentence, and may also be hierarchically defined as chapter:verse,
stanza:line, or paragraph:sentence. Then a list of pairs of starting word number and segment identifier must be
generated. As an example, the pre-processing procedure is performed for the Iliad or biblical books due the the
relatively straightforward structure of the websites.


### Motivation


### Preprocessing
