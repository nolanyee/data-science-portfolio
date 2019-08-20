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
Pitch is directly related to the main frequency of a sound wave. Music audio data is a mixture of sound waves at different frequencies. It can be considered a linear combination of sine and cosine waves of different frequencies, where the sine and cosine components form a basis in terms of which any time shift in the wave can be expressed. To convert the waveform (intensity vs. time) into a spectrum (amplitude vs. frequency), the coefficients of all the different sine and cosine components must be determined. This is done with fast Fourier Transform. The user can specify the range of frequencies for which the coefficients are calculated. Since pitch changes over time, Fourier Transform is performed on a small window, which is moved along the data. The user can specify the window and step size. The transcription region parameters specify where to start transcription and how many steps to take.

<img src="images/MusicFig1.png" width ="900">

It would seem that once the spectra are obtained, the pitches can be determined. Unfortunately, music is not that simple. When most instruments play a note, there is a base frequency that corresponds to pitch. However, there are also harmonics, which correspond to frequencies that are integer multiples of the base frequency (*v*).

<img src="images/MusicFig2.png" width ="600">

Each instrument has a different proportion of each of the harmonics for each pitch. In many cases the base frequency has a lower amplitude than the harmonics. Complicating things even further, some instruments have different harmonic signatures depending on how loudly they are played. In order to determine the actual frequency accurately, deconvolution would have to be done using the harmonic signatures of all relevant instruments and volumes as basis functions. This data, however, was not available for this project, so a major simplification was needed. The harmonic signature was assumed to be uniform for up to a certain number *n* of harmonics (this is the maximum number of harmonics, which can be set by the user).

<img src="images/MusicFig4.png" width ="800">

With this simplification, deconvolution can be done using the Harmonic Sum Spectrum. This spectrum is defined as follows, where *f(v)* is the Fourier Transform spectrum.

<img src="images/MusicFig5.png" width ="150">

Visually it is the sum of spectra that are scaled by one over an integer.

<img src="images/MusicFig3.png" width ="600">

From the example above it is clear that the Harmonic Sum Spectrum has a maximum at the base frequency. For any frequency, the only interference in the Harmonic Sum Spectrum comes from undertones. These are lower notes that have the base frequency as a harmonic. Deconvolution must be performed to subtract the contribution from these lower frequencies. Combining the definition of the assumed harmonic signature with the definition of the Harmonic Sum Spectrum, we obtain the following

<img src="images/MusicFig6.png" width ="500">

Then making a slight approximation the final contribution from the *j*<sup>th</sup> undertone is obtained.

<img src="images/MusicFig7.png" width ="250">

After correction for the contributions from all undertones, the new Harmonic Sum Spectrum is

<img src="images/MusicFig8.png" width ="200">

To avoid noise amplification, undertones lower than 3 Hz are not included in the calculation.

The above approximations allow the program to determine pitch without the used of massive libraries of instrument harmonic signatures. However, because of the approximations, there will inevitably be errors in pitch detection. The most common error is the octave error, where the pitch is detected as being the first harmonic or first undertone rather than the base pitch.

To reduce some of the noise from these calculations, some filtering is done on the spectrum. The user can specify the fraction of the maximum Fourier Transform coefficient below which all coefficients will be set to zero before calculating the Harmonic Sum Spectrum. After the Harmonic Sum Spectrum is calculated, the result is filtered again, removing any signals below the minumum absolute HSS threshold (set by user). Finally, there is also a threshold below which undertone correction is not performed. 

Finally, the corrected base frequencies are converted to pitch using the following formula.

<img src="images/MusicFig10.png" width ="300">

The fuction above is used to bin amplitudes by their pitch. Multiple signals placed in the same pitch bin are summed. The epsilon term is a user defined pitch correction term, expressed in terms of half-tones. This is used to correct for an out of tune instrument or alternate tunings.

The result of this process is called a chromagram. This is what is displayed in the plot windows before the score is output.

### Note Detection
From the chromagram, the transcription step size can be set (as number of chromagram points). This defines wider segments used for note detection and rhythm analysis. The chromagram (binned Harmonic Sum Spectrum) results within each segment are summed in order to reduce noise.

<img src="images/MusicFig11.png" width ="800">

This creates a lower resolution smoothed chromagram, which helps in the note detection steps.

For note detection, the first and second derivatives of the chromagram are calculated for each channel (tone). Derivative calculations often produce random error, so the user can specify a first and second derivative window for smoothing by moving average prior to derivative calculation. 

Note detection relies on identifying maxima in both the signal and the negative second derivative. Maxima are identified as points for which all points within a window around the point being analyzed must be lower than the point being analyzed.

<img src="images/MusicFig12.png" width ="500">

This extrema detection window can be set for both the signal and second derivative. 

The algorithm also matches the position of maxima in the signal and negative second derivative. The tolerance for this match can also be set by the user.

<img src="images/MusicFig13.png" width ="500">

Finally the threshold for note detection can be set. There is an absolute threshold as well as a relative threshold. The absolute threshold prevents detecting noise as notes. The relative threshold (expressed in fraction of maximum intensity across all channels) ensures only the loudest notes are detected.

Once the signal goes above the threshold, note start and end time detection is activated. The note start is defined as the first maximum in the negative second derivative after the threshold is crossed. The note end is defined differently depending on situation. Take this first example (the green circle is a note start, and the red circle is a note end):

<img src="images/MusicFig14.png" width ="500">

If there is no second derivative maximum after the first one, the note end is the point at which the signal falls below the threshold. Moving onto the next example:

<img src="images/MusicFig15.png" width ="500">

Note that the note start corresponds to the negative second derivative maximum regardless of whether there is a maximum in the signal. When there is another second derivative maximum, it marks the end of the note only if it does not correspond to a signal maximum. 

In the next example there is an additional maximum.

<img src="images/MusicFig16.png" width ="500">

In this cases, if there is another negative second derivative maximum that corresponds to a signal maximum, the first note is ended and a second note is started.

If the last negative second derivative maximum corresponds to a signal maximum, the note is ended, a new note is started, and that new note is ended when the signal falls below the threshold.

<img src="images/MusicFig17.png" width ="500">

### Rhythm Alignment
The algorithm above will result in misalignment of many notes because it is unlikely that the maxima will fall in the exact same position for all relevant channels. Therefore note alignment must be performed. The first step is to exclude short notes (the threshold note duration for exclusion can be set by the user).

<img src="images/MusicFig18.png" width ="500">

Then note starts are aligned. The user can set the window within which note starts are all set to the average start time.

<img src="images/MusicFig19.png" width ="500">

Then note ends are aligned with the closest start of any note in any channel, if the time between the note end and other note's start within a user defined window.

<img src="images/MusicFig20b.png" width ="500">

Finally the ends of notes from different channels are aligned with the latest note end before a note start.

<img src="images/MusicFig21.png" width ="500">

Next, the tempo is determined. 



