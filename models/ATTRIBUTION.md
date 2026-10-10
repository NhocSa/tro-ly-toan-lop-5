# Vietnamese offline voice attribution

- Voice: `vi_VN-vais1000-medium`, Piper voice, Vietnamese (`vi_VN`), one speaker, medium quality, 22,050 Hz.
- Model source: [rhasspy/piper-voices, pinned to v1.0.0](https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/vi/vi_VN/vais1000/medium).
- Training data: [VAIS-1000 Vietnamese Speech Synthesis Corpus](https://ieee-dataport.org/documents/vais-1000-vietnamese-speech-synthesis-corpus).
- The model card identifies the dataset license as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The model card is included as `MODEL_CARD.txt`.
- Model SHA-256: `ec7c89e2c85f4d1edc24b6120c18aaf1bda614f06b511567eb9c7c0de15e2dab`.

The bundled voice is a female Vietnamese voice with a northern accent. It works offline after the Piper runtime has been installed by `run.bat`; no voice service API is called when this voice is selected.
