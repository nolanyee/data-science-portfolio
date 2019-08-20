# Music Transcriber
*Skills: Python, Audio Processing*

### Overview
This program is a rudimentary music transcriber. It uses fast Fourier transform to extract the frequency spectrum from a moving time window. The Harmonic Sum Spectrum is used to identify pitches and generate a chromagram. A second derivative peak detection algorithm is used to detect note onset and duration. Note starts and end times are aligned based on overlapping and adjacent notes. Note duration is then assigned to the closest matching assignable note duration. The inaccuracies in the results illustrate challenges in music transcription such as octave errors, interference from harmonics, note decay overlap, and beat detection.

### Usage
The graphical user interface is shown below.

<img src="images/MusicFig9.png" width ="700">

To transcribe an audio file, enter the file path in the settings window. Parameters can be adjusted if necessary. The parameters are explained in following sections. Choose and output format (Treble, Bass, or Treble+Bass). Then press OK to start transcription. A chromagram and note plot will be shown. 
<img src="images/MusicFig23.png" width ="900">

Save these plots if so desired. Then after closing the two windows, the score will display.
<img src="images/MusicFig24.png" width ="800">

## Technical Details
### Pitch Detection
Pitch is directly related to the main frequency of a sound wave. Music audio data is a mixture of sound waves at different frequencies. It can be considered a linear combination of sine and cosine waves of different frequencies, where the sine and cosine components form a basis in terms of which any time shift in the wave can be expressed. To convert the waveform (intensity vs. time) into a spectrum (amplitude vs. frequency), the coefficients of all the different sine and cosine components must be determined. This is done with fast Fourier Transform. Since pitch changes over time, the audio data is split into small time segments. Fourier Transform is performed on each segment.

<img src="images/MusicFig1.png" width ="900">

It would seem that once the spectra are obtained, the pitches can be determined. Unfortunately, music is not that simple. When most instruments play a note, there is a base frequency that corresponds to pitch. However, there are also harmonics, which correspond to frequencies that are integer multiples of the base frequency.

<img src="images/MusicFig2.png" width ="900">


