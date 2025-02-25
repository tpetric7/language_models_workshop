# -*- coding: utf-8 -*-
"""Transcribe_with_Whisper.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_3Qqjpw-pIYEy7xlLDlgS9Gjfgp863zW
"""

!pip install git+https://github.com/openai/whisper.git
!sudo apt update && sudo apt install ffmpeg

!whisper "/content/Life_After_AI_Takes_Our_Jobs_The_Rocky_Road_to_2035_(Complete_Timeline).mp4" --model medium

# prompt: download the transcription files to local disk

from google.colab import files
files.download('/content/Life_After_AI_Takes_Our_Jobs_The_Rocky_Road_to_2035_(Complete_Timeline).srt')
files.download('/content/Life_After_AI_Takes_Our_Jobs_The_Rocky_Road_to_2035_(Complete_Timeline).txt')