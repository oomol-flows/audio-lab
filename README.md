<div align=center>
	<h1>Audio Lab</h1>
	<p><a href="https://hub.oomol.com/package/audio-lab?open=true" target="_blank"><img src="https://static.oomol.com/assets/button.svg" alt="Open in OOMOL Studio" /></a></p>
</div>

## Overview

Audio Lab is a comprehensive audio processing toolkit that enables seamless conversion between text and speech. This package provides professional-grade text-to-speech synthesis and speech-to-text transcription capabilities, making it perfect for content creators, accessibility applications, and automated transcription workflows.

## Features

### 🎙️ Text to Audio Conversion
- **Natural Voice Synthesis**: Convert any text into lifelike speech using advanced AI voice technology
- **Multiple Voice Options**: Choose from 5 distinct Chinese voice personalities:
  - 冷酷哥哥 (Cool Brother) - Multi-emotional male voice
  - 甜心小美 (Sweet Little Sister) - Multi-emotional female voice  
  - 高冷御姐 (Cold Queen) - Multi-emotional sophisticated female voice
  - 京腔侃爷 (Beijing Dialect Chatty Uncle) - Multi-emotional Beijing accent male voice
  - 温柔女神 (Gentle Goddess) - Soft female voice
- **Custom Output**: Specify custom filenames and save locations for generated audio files
- **MP3 Format**: High-quality audio output in universally compatible MP3 format

### 📝 Speech to Text Transcription
- **Accurate Transcription**: Convert spoken audio into precise text using advanced speech recognition
- **Multi-format Support**: Process various audio formats including MP3, WAV, FLAC, M4A, AAC, OGG, and WMA
- **Automatic Language Detection**: Intelligent language recognition for optimal transcription accuracy
- **Cloud Integration**: Seamless upload and processing of audio files through cloud storage

## Quick Start

### Text to Audio Workflow
1. **Input Your Text**: Enter any text content you want to convert to speech
2. **Choose Voice**: Select your preferred voice personality from the dropdown menu
3. **Set Output Location**: Specify where to save the generated audio file
4. **Generate Audio**: Run the task to create your speech audio file
5. **Preview Results**: Listen to the generated audio directly in the interface

### Speech to Text Workflow
1. **Upload Audio File**: Select your audio file using the file picker
2. **Automatic Processing**: The system uploads your file and begins transcription
3. **Get Transcription**: Receive accurate text transcription of your audio content
4. **Review Results**: View the transcribed text in the preview interface

## Use Cases

- **Content Creation**: Generate voiceovers for videos, podcasts, and presentations
- **Accessibility**: Create audio versions of written content for visually impaired users
- **Language Learning**: Practice pronunciation with native speaker voice samples
- **Meeting Transcription**: Convert recorded meetings and interviews to text
- **Automated Workflows**: Build pipelines that process audio content at scale

## Technical Details

### Text to Audio Task
- **Input**: Text content, voice selection, output directory, optional custom filename
- **Output**: MP3 audio file path
- **Processing**: Uses Volcengine TTS API with retry logic and status polling

### Speech to Text Task  
- **Input**: Remote audio file URL
- **Output**: Transcribed text string
- **Processing**: Uses Volcengine STT API with automatic format detection

### Speech to Text Subflow
- **Input**: Local audio file
- **Output**: Transcribed text
- **Processing**: Handles file upload to cloud storage followed by transcription

## Integration Example

The included demo workflow demonstrates a complete round-trip process:
1. Convert text to audio using selected voice
2. Preview the generated audio
3. Upload audio to cloud storage
4. Transcribe the audio back to text
5. Display the final transcription for comparison

This showcases the quality and accuracy of both text-to-speech and speech-to-text capabilities.