# Text-to-Speech Service using ElevenLabs

A Python service for converting text to speech using the ElevenLabs API. This service provides both a programmatic interface and a command-line tool for generating high-quality speech audio from text.

## Features

- 🎵 High-quality text-to-speech using ElevenLabs API
- 🎙️ Multiple voice options and voice selection by name or ID
- ⚙️ Customizable voice settings (stability, similarity boost, style)
- 🌍 Support for multiple models including multilingual options
- 💰 Cost estimation and account quota tracking
- 🖥️ Command-line interface for easy usage
- 📁 Organized output management
- 🛡️ Comprehensive error handling

## Prerequisites

- Python 3.7 or higher
- ElevenLabs API key (get one at [elevenlabs.io](https://elevenlabs.io))

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Copy `.env.template` to `.env`
   - Edit `.env` and add your ElevenLabs API key:
     ```
     ELEVENLABS_API_KEY=your_actual_api_key_here
     ```

## Quick Start

### Using the Command Line Interface

```bash
# Simple text-to-speech
python cli.py "Hello, world!"

# Use a specific voice
python cli.py "Hello, world!" --voice-name "Rachel"

# Convert text from a file
python cli.py --text-file "story.txt" --output "audiobook.mp3"

# List available voices
python cli.py --list-voices

# Check your account information
python cli.py --account-info

# Estimate cost before conversion
python cli.py "Your text here" --estimate-cost
```

### Using the Python API

```python
from src.text_to_speech_service import TextToSpeechService

# Initialize the service
tts = TextToSpeechService()

# Convert text to speech
output_file = tts.text_to_speech("Hello, world!")
print(f"Audio saved to: {output_file}")

# Use custom voice settings
voice_settings = {
    "stability": 0.7,
    "similarity_boost": 0.8,
    "style": 0.2,
    "use_speaker_boost": True
}

output_file = tts.text_to_speech(
    text="Custom voice settings example",
    voice_settings=voice_settings,
    output_filename="custom_voice.mp3"
)
```

## Configuration

The `.env` file supports the following configuration options:

```bash
# Required: Your ElevenLabs API key
ELEVENLABS_API_KEY=your_api_key_here

# Optional: Default voice ID (Rachel voice)
DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Optional: Output directory for audio files
OUTPUT_DIR=output

# Optional: Default audio format
AUDIO_FORMAT=mp3

# Optional: Default model
MODEL=eleven_monolingual_v1
```

## Voice Settings

You can customize the voice output using these parameters:

- **stability** (0.0-1.0): Controls voice stability. Higher values make the voice more consistent but potentially less expressive.
- **similarity_boost** (0.0-1.0): Enhances voice similarity to the original speaker. Higher values make the voice closer to the training data.
- **style** (0.0-1.0): Controls the style and expressiveness of the voice. Higher values add more variation and emotion.
- **use_speaker_boost** (boolean): Enhances speaker similarity and overall quality.

## Available Models

- `eleven_monolingual_v1`: Optimized for English, fastest and most reliable
- `eleven_multilingual_v2`: Supports multiple languages with high quality
- `eleven_multilingual_v1`: Legacy multilingual model

## Command Line Options

```bash
python cli.py [OPTIONS] [TEXT]

Positional arguments:
  TEXT                  Text to convert to speech

Options:
  -h, --help           Show help message
  -f, --text-file      Path to text file to convert
  -v, --voice-id       Voice ID to use for synthesis
  -n, --voice-name     Voice name to use for synthesis
  -o, --output         Output filename for audio file
  -m, --model          Model to use (eleven_monolingual_v1, eleven_multilingual_v2, etc.)
  --stability          Voice stability (0.0-1.0, default: 0.5)
  --similarity-boost   Voice similarity boost (0.0-1.0, default: 0.5)
  --style              Voice style (0.0-1.0, default: 0.0)
  --list-voices        List available voices and exit
  --account-info       Show account information and exit
  --estimate-cost      Estimate cost for the text and exit
```

## Examples

Run the example scripts to see the service in action:

```bash
# Simple example
python examples/simple_example.py

# Advanced example with voice customization
python examples/advanced_example.py
```

## API Reference

### TextToSpeechService Class

#### `__init__(api_key=None)`
Initialize the service with an optional API key.

#### `text_to_speech(text, voice_id=None, model=None, voice_settings=None, output_filename=None)`
Convert text to speech and save as audio file.

#### `get_available_voices()`
Get list of available voices from ElevenLabs.

#### `get_voice_by_name(name)`
Find a voice by name.

#### `get_account_info()`
Get account information including character quota.

#### `estimate_cost(text)`
Estimate the cost/character usage for given text.

## Error Handling

The service includes comprehensive error handling for:
- Invalid API keys
- Network connectivity issues
- File I/O errors
- Invalid voice IDs or names
- Character quota exceeded
- Invalid text input

## File Structure

```
text2speach/
├── src/
│   └── text_to_speech_service.py  # Main service class
├── examples/
│   ├── simple_example.py          # Basic usage example
│   └── advanced_example.py        # Advanced features example
├── output/                        # Generated audio files
├── cli.py                         # Command-line interface
├── requirements.txt               # Python dependencies
├── .env.template                  # Environment template
├── .env                          # Your environment configuration
└── README.md                     # This file
```

## Troubleshooting

### Common Issues

1. **"ElevenLabs API key is required"**
   - Make sure your `.env` file contains a valid API key
   - Ensure the API key is not set to `your_api_key_here`

2. **"Failed to generate speech"**
   - Check your internet connection
   - Verify your API key is valid and has remaining quota
   - Ensure the voice ID exists

3. **"Voice not found"**
   - Use `python cli.py --list-voices` to see available voices
   - Check voice name spelling (case-insensitive)

4. **Import errors**
   - Run `pip install -r requirements.txt` to install dependencies
   - Ensure you're in the correct directory

## Cost and Quota

ElevenLabs pricing (approximate):
- **Free tier**: 10,000 characters per month
- **Starter**: $5/month for 30,000 characters  
- **Creator**: $11/month for 100,000 characters

Use `--estimate-cost` or `--account-info` to monitor usage.

## License

This project is licensed under the MIT License.

## Support

For issues related to:
- This service: Create an issue in this repository
- ElevenLabs API: Visit [ElevenLabs documentation](https://docs.elevenlabs.io/)
- Voice availability: Check your ElevenLabs account settings