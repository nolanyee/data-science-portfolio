'''
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
'''

import urllib.request
from bs4 import BeautifulSoup as bs
import re
import nltk
import gensim
import numpy as np
from scipy.stats import binom
from matplotlib import pyplot as plt
from matplotlib import patches
from math import e,sqrt

# Extraction of text from website and storage of verse locations
verselist = []
tokencount = 0
book = None

# Loading and preprocessing for Biblical analysis
def bible(bookname,startchapter,endchapter):
    global verselist
    global tokencount
    global book
    for i in range(int(startchapter), int(endchapter+1)): # Verse separation procedure depends on html structure
        url = 'https://nasb.literalword.com/?q='+str(bookname)+'+'+ str(i)
        html = urllib.request.urlopen(url).read().decode('utf8')
        soup = bs(html, 'html.parser')
        verses = soup.find_all('span')
        chapter = 0
        for x in verses: # Tokenization
            line = bs.get_text(x)
            tokens = nltk.word_tokenize(line)
            if len(tokens) > 1 and re.search('\d+:?\d*', tokens[0]): # Creation of token list and verse reference list
                if re.search('\d+:+\d+', tokens[0]):
                    colon = tokens[0].index(':')
                    chapter = tokens[0][:colon]
                else:
                    tokens[0] = str(chapter) + ':' + tokens[0]
                verselist.append([tokencount, tokens.pop(0)])
                tokencount += len(tokens)
                if not book:
                    book = tokens
                else:
                    book += tokens

# Loading and preprocessing for Homer's Iliad
def iliad(startref, endref):
    global verselist
    global tokencount
    global book
    url = 'http://www.uh.edu/~cldue/texts/iliad.html'
    html = urllib.request.urlopen(url).read().decode('utf8')
    soup = bs(html, 'html.parser')
    verses = [re.sub(r'[\n,\xa0]', ' ', x.get_text()) for x in soup.find_all('p')]
    verses = [re.sub(r'[\[\]]', '', x) for x in verses]
    verses = [x for x in verses if (len(x) > 0) & (x != ' ')]
    verses = verses[3:]
    romannumeraldict = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
                        'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18,
                        'XIX': 19, 'XX': 20,
                        'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24}
    scroll = None
    def parseref(ref):
        return ref[:ref.index(':')], ref[ref.index(':')+1:]
    startbook, startline = parseref(startref)
    endbook, endline = parseref(endref)
    for x in verses:
        if x[:7] == 'SCROLL ':
            scroll = str(romannumeraldict[x[7:]])
        else:
            if scroll >= startbook and scroll <= endbook:
                line = x[:x.index(' ')]
                reference = scroll + ':' + line
                if not (scroll == startbook and int(line)<int(startline)) \
                        and not (scroll == endbook and int(line)>int(endline)):
                    truncx = x[len(line):]
                    tokens = nltk.word_tokenize(truncx)
                    verselist.append([tokencount, reference])
                    tokencount += len(tokens)
                    if not book:
                        book = tokens
                    else:
                        book += tokens

# Lemmatization
def lemmatize():
    global lemmatizedbook
    lemmatizedbook = book[:]
    for i in range(0, len(lemmatizedbook)):
        lemmatizedbook[i] = nltk.stem.WordNetLemmatizer().lemmatize(lemmatizedbook[i], pos='v')
        lemmatizedbook[i] = lemmatizedbook[i].lower()

# Stemming
def stem():
    global stemmedbook
    stemmedbook = lemmatizedbook[:]
    for i in range(0, len(stemmedbook)):
        stemmedbook[i] = nltk.stem.porter.PorterStemmer().stem(stemmedbook[i])

# Custom Stop Word List
stopwords = ['a','an','the','no','not','nor','t','too', 'also','and','or','so','if','then',
             'for','as','of','to','at','in', 'on','with','by','into','off','from','s',
             'i','me','my','you','your','yours','he','him','his','she','her','hers','it','its',
             'we','us','our','ours','but','they','them','their','theirs',
             'be','am','are','is','was','were','been','being','will',
             'do','does','did','doing','don',
             'have','has','had','having','some','shall','should','can','could','would',
             'until','about','such',
             'there','this','that','these','those','here','where','which','who','whom','what','when','while','how',
             'very', 'more','each','any','same','just','than']

punctuation = ['.',',',':',';','"',"'","''","`","``",'?','!','“','”']

# Returns sets of related words (synonyms, synonyms + antonyms) for a word (idea set)
def relatedwords(word):
    synonyms = [word]
    antonyms = []
    for synset in nltk.corpus.wordnet.synsets(word):
        if word in synset.name() or nltk.stem.porter.PorterStemmer().stem(word) in synset.name():
            for lemma in synset.lemmas():
                synonyms.append(lemma.name())
                if lemma.antonyms():
                    antonyms.append(lemma.antonyms()[0].name())
    synonymset = set(synonyms)
    relatedset = synonymset.union(antonyms)
    return (synonymset, relatedset)

# Generates list of idea sets (sets of related words) for each word in the book
def generateideas():
    global idealist
    global idealist2
    global worddict
    idealist = []
    idealist2 = []
    worddict = {}
    for x in lemmatizedbook:
        if x not in stopwords and x not in worddict:
            related = relatedwords(x)
            idealist.append(related[0])
            idealist2.append(related[1])
            worddict.update({x: 1})
        elif x in worddict:
            worddict[x] += 1

# Removes from the idea sets any word not in the book
def trimideas(ilist):
    ilistcopy = ilist[:]
    for i in range(0,len(ilist)):
        for y in list(ilist[i]):
            if y not in worddict:
                ilistcopy[i] = ilistcopy[i].difference([y])
    return ilistcopy

# Returns the word in a list that occurs most frequently in the book
def maxword(wlist):
    maxcount = 0
    maxword = None
    for x in wlist:
        count = worddict[x]
        if count > maxcount:
            maxcount = count
            maxword = x
    return maxword

# Union idea sets with non-empty intersections
def mergeideas(setlist):
    setlistcopy = setlist[:]
    for i in range(0,len(setlist)):
        for j in range(0,len(setlist)):
            if setlistcopy[i].intersection(setlist[j])!=set():
                setlistcopy[i]= setlistcopy[i].union(setlist[j])
        synlist = list(setlistcopy[i])
        setlistcopy[i]=[synlist,maxword(synlist)]
    reducedlist = []
    for x in setlistcopy:
        if x not in reducedlist:
            reducedlist.append(x)
    return reducedlist

# Generate a book replacing each word with the most frequent word in the associated idea set
def generateideabooks():
    global ideabook
    global ideabook2
    ideabook = []
    for x in lemmatizedbook:
        if x in stopwords:
            ideabook.append('.')
        else:
            for y in idealist:
                if x in y[0]:
                    ideabook.append(y[1])
                    break
    ideabook2 = []
    for x in lemmatizedbook:
        if x in stopwords:
            ideabook2.append('.')
        else:
            for y in idealist2:
                if x in y[0]:
                    ideabook2.append(y[1])
                    break

# Lemmatization, Stemming, Idea Generation
def lemstemidea():
    global idealist
    global idealist2
    lemmatize()
    stem()
    generateideas()
    idealist = trimideas(idealist)
    idealist2 = trimideas(idealist2)
    idealist = mergeideas(idealist)
    idealist2 = mergeideas(idealist2)
    generateideabooks()

def wordoverlap(list1,list2): # Jaccard similarity coefficient
    return len(set(list1).intersection(list2).difference(punctuation))/len((set(list1+list2)).difference(punctuation))

# Extend shorter list to match length of longer list by adding duplicates of elements of shorter list
def extendlists(pos1, pos2): # pos1 larger than pos2
    placement = []
    copypos1 = pos1[:]
    # If all shorter list average is larger than longer list, order of element assignment to longer list is reversed
    if sum(pos1)/len(pos1)<sum(pos2)/len(pos2):
        a = range(len(pos2)-1,-1,-1)
    else:
        a=range(0,len(pos2))
    # Assign each element of shorter list to closest element of longer list
    for x in a:
        min = 10000
        minpos = None
        for y in copypos1:
            if abs(pos2[x] - y) < min:
                min = abs(pos2[x] - y)
                minpos = y
        placement.append(minpos)
        copypos1.remove(minpos)
    if sum(pos1) / len(pos1) < sum(pos2) / len(pos2):
        placement.reverse()
    extendedpos2 = []
    for x in pos1: # Elements in longer list without assignment are assigned copies of closest element in short list
        if x in placement:
            extendedpos2.append(pos2[placement.index(x)])
        else:
            min = 10000
            minpos = None
            for y in pos2:
                if abs(x - y) < min:
                    min = abs(x - y)
                    minpos = y
            extendedpos2.append(minpos)
    return extendedpos2

# Determine the similarity in word order
def ordersimilarity(list1,list2):
    shared = list(set(list1).intersection(list2).difference(punctuation))
    if shared: # Create lists of word positions for each word shared in 2 lists
        positions1 = []
        positions2 = []
        for i in range(0,len(shared)):
            counts1 = 0
            counts2 = 0
            for j in range(0,len(list1)):
                if list1[j]==shared[i]:
                    if counts1==0:
                        positions1.append([j])
                    else:
                        positions1[i].append(j)
                    counts1+=1
            for j in range(0,len(list2)):
                if list2[j]==shared[i]:
                    if counts2==0:
                        positions2.append([j])
                    else:
                        positions2[i].append(j)
                    counts2+=1
        for i in range(0,len(shared)): # Extend shorter lists to match corresponding longer lists
            if len(positions1[i])>len(positions2[i]):
                positions2[i]=extendlists(positions1[i],positions2[i])
            elif len(positions1[i])<len(positions2[i]):
                positions1[i]=extendlists(positions2[i], positions1[i])
        vector1 = []
        vector2 = []
        for i in range(0,len(shared)): # Create vector of word positions
            for j in range(0,len(positions1[i])):
                vector1.append(positions1[i][j])
                vector2.append(positions2[i][j])
        vector1 = np.array(vector1)
        vector2 = np.array(vector2)
        # Calculate order similarity as 1-||v1-v2||/||v1+v2||
        differencevectors = vector1-vector2
        sumvectors = vector1+vector2
        normsqdiff = sqrt(np.dot(differencevectors,differencevectors))
        normsqsum = sqrt(np.dot(sumvectors,sumvectors))
        if normsqsum == 0:
            return 0
        else:
            return 1-normsqdiff/normsqsum
    else:
        return 0

# Total similarity is word overlap times weighted word order
def totalsimilarity(list1,list2,alpha=1):
    return wordoverlap(list1, list2)*ordersimilarity(list1,list2)**alpha

# Returns maximum match of smaller passage to equal-sized subpassage in larger passage, and weights based on length
def movingsimilarity(list1,list2,alpha): # list1 smaller than list2
    similarity = totalsimilarity(list1,list2,alpha)
    window = len(list1)
    for i in range(0,len(list2)-window+1):
        temp = totalsimilarity(list1,list2[i:i+window],alpha)
        if temp > similarity:
            similarity = temp
    return similarity/(1+e**(-1*window+5))

# Returns word frequency list
def frequency(wordlist,number=None):
    count = 0 # Number of punctuation and stopwords are excluded
    for x in punctuation:
        if x in wordlist:
            count+=1
    for x in stopwords:
        if x in wordlist:
            count+=1
    if number:
        dist = nltk.FreqDist(nltk.Text(wordlist)).most_common(number+count)
    else:
        dist = nltk.FreqDist(nltk.Text(wordlist))
    dist = [x for x in dist if x[0] not in punctuation and x[0] not in stopwords][:number]
    return dist

# Returns verse number given word number
def versenumber(number):
    for i in range(0,len(verselist)):
        if i != len(verselist)-1:
            if verselist[i][0]<=number<verselist[i+1][0]:
                return verselist[i][1]
        else:
            return verselist[-1][1]

# Returns probability of having an equal or greater word density if words were randomly uniformly distributed
def binomial(word,verse,book):
    freq = book.count(word)/len(book)
    cumulative = 0
    for i in range(verse.count(word),len(verse)+1):
        cumulative+=binom.pmf(i,len(verse),freq)
    return cumulative

# Plots a series onto a word intentionality plot
def densityplot(word,book,window=1):
    xlabels = []
    yvalues = []
    margin = (window - 1) // 2
    for i in range(0, len(verselist)):
        xlabels.append(verselist[i][1])
        if i<len(verselist)-1-margin and margin<i:
            yvalues.append(1-binomial(word, book[verselist[i-margin][0]:verselist[i+margin + 1][0]], book))
        elif i>=len(verselist)-1-(window-1)//2:
            yvalues.append(1-binomial(word, book[verselist[i-margin][0]:], book))
        else:
            yvalues.append(1 - binomial(word, book[:verselist[i+margin+1][0]], book))
    ax1.plot(xlabels,yvalues,label=word)
    ax1.set_title('Word Intentionality Plot')
    ax1.set_xlabel('Verse')
    ax1.set_ylabel('Intentionality Probability')
    ax1.set_xticklabels(xlabels,rotation=90)
    ax1.legend()

# Generates word intentionality plot
# Window must be smaller than length of book
def plotworddensity(book1=None,words=None,book2=None,number=None,threshold=None,window=15):
    if book1 and words:
        for i in range(0,len(words)):
            densityplot(words[i], book1,window)
    if book2:
        wordlist = frequency(book2, 1000)
        if threshold:
            if not number:
                for i in range(0, len(wordlist)):
                    if wordlist[i][1] >= threshold:
                        densityplot(wordlist[i][0], book2, window)
            else:
                for i in range(0, number):
                    if wordlist[i][1] >= threshold:
                        densityplot(wordlist[i][0], book2, window)
        if number and not threshold:
            wordlist = frequency(book2, 1000)
            for i in range(0, number):
                densityplot(wordlist[i][0], book2, window)

# Creates an arc plot showing degree of parallelism between verses
def arcplot(book,alpha,threshold,window=1): # Window must be smaller than length of book
    verses = len(verselist)
    margin = (window-1)//2
    yvalues = [0 for x in verselist]
    xlabels = [x[1] for x in verselist]
    ax2.plot(xlabels, yvalues)
    ax2.set_title('Parallelism Arc Plot')
    ax2.set_xlabel('Verse')
    ax2.set_xticklabels(xlabels, rotation=90)
    ax2.set_yticklabels(yvalues, color=(1,1,1))
    ax2.set_ylim((0,(len(xlabels)-1)//2))
    for i in range(0,verses):
        for j in range(i+1,verses):
            if margin < i < verses-1-margin:
                a = book[verselist[i-margin][0]:verselist[i + 1+margin][0]]
            elif i >= verses-1-margin:
                a = book[verselist[i-margin][0]:]
            else:
                a = book[:verselist[i+1+margin][0]]
            if margin <j < verses-1-margin:
                b = book[verselist[j-margin][0]:verselist[j + 1+margin][0]]
            elif j >= verses-1-margin:
                b = book[verselist[j-margin][0]:]
            else:
                b = book[:verselist[j+1+margin][0]]
            if a>=b:
                similarity = movingsimilarity(b,a,alpha)
            else:
                similarity = movingsimilarity(a,b,alpha)
            if similarity >= threshold:
                val = 1-(similarity-threshold)/(1-threshold)
                arc = patches.Arc(((i+j)/2, 0), abs(i-j), abs(i-j),0,0,180,color=(val,val,val))
                ax2.add_patch(arc)

# Models topics on passage using Latent Dirichlet Allocation
def topicmodel(book,window,generalize=1,numpass=2,filtlow=2,filthigh=0.8,filtmax=1000):
    verses = len(verselist)
    windowlist = []
    xlabels = []
    while verses//window <= 2:
        window = window-1
    for i in range(0,verses//window): # Breaks passage into sections (documents)
        if i < verses//window-1:
            fulllist = book[verselist[i*window][0]:verselist[(i+1)*window][0]][:]
            xlabel = str(verselist[i*window][1])+str(verselist[(i+1)*window][1])
        else:
            fulllist = book[verselist[i * window][0]:]
            xlabel = str(verselist[i * window][1])+ '-' + str(verselist[-1][1])
        xlabels.append(xlabel)
        reducedlist = []
        for x in fulllist:
            if x not in punctuation:
                reducedlist.append(x)
        windowlist.append(reducedlist)
    # Create dictionary, filter, calculate idf, calculate LDA
    dictionary = gensim.corpora.Dictionary(windowlist)
    dictionary.filter_extremes(no_below=filtlow,no_above=filthigh,keep_n=filtmax)
    bagsofwords = [dictionary.doc2bow(x) for x in windowlist]
    bowtfidf = gensim.models.TfidfModel(bagsofwords)[bagsofwords]
    LDAmodel = gensim.models.LdaModel(bowtfidf,num_topics=max(verses//(window*generalize),1),
                                      id2word=dictionary,passes=numpass)
    for a,b in LDAmodel.print_topics(-1):
        print('Topic'+str(a)+':'+str(b))
    plotmatrix = []
    for j in range(0,len(bagsofwords)): # Plots topic probabilities
        docvector = []
        assignment = sorted(LDAmodel[bagsofwords[j]],key=lambda a:-1*a[1])
        topiclist = [a[0] for a in assignment]
        for k in range(0,verses//(window*generalize)):
            if k in topiclist:
                docvector.append([a[1]for a in assignment if a[0]==k][0])
            else:
                docvector.append(0)
        plotmatrix.append(docvector)
    plotmatrix = np.array(plotmatrix).transpose()
    for i in range(0,len(plotmatrix)):
        ax3.plot(xlabels,plotmatrix[i],label='Topic '+str(i))
    ax3.set_title('Topic Plot')
    ax3.set_xlabel('Verse Range')
    ax3.set_ylabel('Topic Probability')
    ax3.set_xticklabels(xlabels, rotation=90)
    ax3.legend()

# Custom Lexical Dispersion Plot
def lexicaldispersion(book,number=None,words=None):
    if number and not words:
        wordlist = [x[0] for x in frequency(book, number)]
    elif words and not number:
        wordlist = words
    elif words and number:
        wordlist = words+[x[0] for x in frequency(book, number)]
    else:
        wordlist = []
    xlabels = []
    scatterx = []
    scattery = []
    size = [] # Size of bars represents number of times word appears in verse
    for a in wordlist:
        for i in range(0,len(verselist)):
            xlabels.append(verselist[i][1])
            if i < len(verselist)-1:
                verse = book[verselist[i][0]:verselist[i+1][0]]
            else:
                verse = book[verselist[i][0]:]
            size.append(10*verse.count(a)**2)
            scatterx.append(verselist[i][1])
            scattery.append(a)
    ax4.scatter(scatterx,scattery,s=size,marker='|')
    ax4.set_title('Lexical Dispersion Plot')
    ax4.set_xlabel('Verse')
    ax4.set_ylabel('Word')
    ax4.set_xticklabels(xlabels, rotation=90)

density_fig, ax1 = plt.subplots()
arc_fig, ax2 = plt.subplots()
topic_fig, ax3 = plt.subplots()
lexical_fig, ax4 = plt.subplots()

# Perform Analysis
def analyze(freqbook='lemmatizedbook', freqnum=100,
            densitybook1=None, densitywords = None, densitybook2 = 'default', densitythreshold = 25,
            arcbook = 'ideabook2', alpha=0.1, arcthreshold=0.3, arcwindow=1,
            topicbook = 'ideabook',topicwindow = 10, topicgeneralize = 2,
            dispersionbook = 'lemmatizedbook', dispersionnum = 10, dispersionwords = None):
    lemstemidea()
    print('Book:')
    print(book)
    print('Lemmatized:')
    print(lemmatizedbook)
    print('Stemmed:')
    print(stemmedbook)
    print('Synsets:')
    print(idealist)
    print('Including Antonyms:')
    print(idealist2)
    print('Ideas:')
    print(ideabook)
    print('Including Contrasts:')
    print(ideabook2)
    print('Frequency Distribution:')
    print(frequency(globals()[freqbook], freqnum))
    if densitybook2 == 'default':
        densitybook2 = globals()['ideabook2']
    elif densitybook2 != None:
        densitybook2 = globals()[densitybook2]
    if densitybook1 != None:
        densitybook1 = globals()[densitybook1]
    plotworddensity(book1=densitybook1,words=densitywords,book2=densitybook2, threshold=densitythreshold)
    arcplot(globals()[arcbook], alpha, arcthreshold, arcwindow)
    topicmodel(globals()[topicbook], topicwindow, topicgeneralize)
    lexicaldispersion(globals()[dispersionbook], dispersionnum, dispersionwords)
    plt.show()

if __name__ == '__main__':
    print('The following is a demonstration of the literary analysis tools using the Iliad or'+
          ' biblical books as the example texts.')
    biblebook = input('Book name: ')
    if biblebook == 'Iliad':
        startref = input('Start Reference (Book:Line): ')
        endref = input('End Reference (Book:Line): ')
        iliad(startref, endref)
    else:
        startchapter = input('Start Chapter: ')
        endchapter = input('End Chapter: ')
        bible(biblebook,int(startchapter),int(endchapter))
    usedefault = input('Use default settings? (yes/no): ')
    if usedefault == 'yes':
        analyze()
    else:
        kwargs = {'freqbook': 'lemmatizedbook', 'freqnum': 100,
                  'densitybook1': None, 'densitywords': None, 'densitybook2': 'ideabook2', 'densitythreshold': 25,
                  'arcbook': 'ideabook2', 'alpha': 0.1, 'arcthreshold': 0.3, 'arcwindow': 1,
                  'topicbook': 'ideabook', 'topicwindow': 10, 'topicgeneralize': 2,
                  'dispersionbook': 'lemmatizedbook', 'dispersionnum': 10, 'dispersionwords': None}
        edit = 'yes'
        print('When editing parameters, be careful with spelling.')
        while edit == 'yes':
            editfunction = input('Function (frequency, density, arc, topic, lexical):')
            if editfunction == 'frequency':
                kwargs['freqbook'] = input('Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2): ')
                kwargs['freqnum'] = int(input('Number of Words: '))
            elif editfunction == 'density':
                print('Note: Both Search Book and Wordlist must be None if Words in Book is not None.')
                densbook1input = input('Search Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2, None): ')
                if densbook1input == 'None':
                    kwargs['densitybook1'] = None
                else:
                    kwargs['densitybook1'] = densbook1input
                denswordsinput = input('Word list (comma separated) or None: ')
                if denswordsinput == 'None':
                    kwargs['densitywords'] = None
                else:
                    kwargs['densitywords'] = re.split(r' *[,.] *', denswordsinput)
                densbook2input = input('Words in Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2, None): ')
                if densbook2input == 'None':
                    kwargs['densitybook2'] = None
                else:
                    kwargs['densitybook2'] = densbook2input
                densthresholdinput = int(input('Threshold: '))
            elif editfunction == 'arc':
                kwargs['arcbook'] = input('Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2): ')
                kwargs['alpha'] = float(input('Alpha: '))
                kwargs['arcthreshold'] = float(input('Threshold: '))
                kwargs['arcwindow'] = int(input('Window: '))
            elif editfunction == 'topic':
                kwargs['topicbook'] = input('Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2): ')
                kwargs['topicwindow'] = int(input('Window: '))
                kwargs['topicgeneralize'] = int(input('Generalization Factor: '))
            elif editfunction == 'lexical':
                kwargs['dispersionbook'] = input('Book (book, lemmatizedbook, stemmedbook, ideabook, ideabook2): ')
                lexicalnuminput = input('Number of Top Words or None: ')
                if lexicalnuminput == 'None':
                    kwargs['dispersionnum'] = None
                else:
                    kwargs['dispersionnum'] = int(lexicalnuminput)
                lexicalwordsinput = input('Word list (comma separated) or None: ')
                if lexicalwordsinput == 'None':
                    kwargs['dispersionwords'] = None
                else:
                    kwargs['dispersionwords']  = re.split(r' *[,.] *', lexicalwordsinput)
            else:
                print('Invalid Entry')
            edit = input('Continue Editing? (yes/no):')
        analyze(**kwargs)
else:
    print('Define global variable "book" as a list of tokens in the text')
    print('Define global variable "verselist" as a list of tuples each containing (word number, "chapter:verse") ')
    print('Then run lemstemidea() and the desired plotting function to calculate plots, or analyze() for all plots.')
    print('Display all plots using plot.show() \n'
          'or individual plots with density_fig.show(), arc_fig.show(), topic_fig.show(), lexical_fig.show()')