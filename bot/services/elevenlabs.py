#!/usr/bin/env python3
"""
Consolidated Text-to-Speech CLI using ElevenLabs API
All functionality in a single file
"""

import argparse
import sys
import os
import requests
import time
import re
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TextToSpeechService:
    """
    A service for converting text to speech using ElevenLabs API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError("ElevenLabs API key is required. Please set ELEVENLABS_API_KEY in .env file")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = os.getenv('DEFAULT_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
        self.default_model = os.getenv('MODEL', 'eleven_monolingual_v1')
        self.output_dir = Path(os.getenv('OUTPUT_DIR', 'output'))
        self.audio_format = os.getenv('AUDIO_FORMAT', 'ogg')  # Default to OGG for Telegram voice messages
        
        self.output_dir.mkdir(exist_ok=True)
        
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
    

    def get_audio_quality_presets(self) -> Dict[str, Dict]:
        return {
            "podcast": {"stability": 0.7, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True, "description": "Optimized for podcast narration"},
            "audiobook": {"stability": 0.8, "similarity_boost": 0.9, "style": 0.2, "use_speaker_boost": True, "description": "Perfect for audiobooks"},
            "conversational": {"stability": 0.4, "similarity_boost": 0.6, "style": 0.6, "use_speaker_boost": True, "description": "Natural conversation style"},
            "professional": {"stability": 0.9, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "description": "Professional presentations"},
            "expressive": {"stability": 0.3, "similarity_boost": 0.5, "style": 0.8, "use_speaker_boost": True, "description": "Highly expressive delivery"},
            "news": {"stability": 0.8, "similarity_boost": 0.7, "style": 0.1, "use_speaker_boost": True, "description": "Clear news reading"}
        }
    
    def apply_quality_preset(self, preset_name: str) -> Dict:
        presets = self.get_audio_quality_presets()
        if preset_name.lower() not in presets:
            available = ", ".join(presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
        preset = presets[preset_name.lower()]
        return {k: v for k, v in preset.items() if k != "description"}
    
    def _validate_voice_settings(self, voice_settings: Dict) -> None:
        if not isinstance(voice_settings, dict):
            raise ValueError("voice_settings must be a dictionary")
        valid_settings = {'stability': (0.0, 1.0), 'similarity_boost': (0.0, 1.0), 'style': (0.0, 1.0), 'use_speaker_boost': (bool,)}
        for key, value in voice_settings.items():
            if key in valid_settings:
                if key == 'use_speaker_boost':
                    if not isinstance(value, bool):
                        raise ValueError(f"'{key}' must be a boolean")
                else:
                    min_val, max_val = valid_settings[key]
                    if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                        raise ValueError(f"'{key}' must be between {min_val} and {max_val}")
    
    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename).strip(' .')
        return sanitized if sanitized else f"speech_{int(time.time())}"
    
    def text_to_speech(self, text: str, voice_id: Optional[str] = None, model: Optional[str] = None, 
                      voice_settings: Optional[Dict] = None, quality_preset: Optional[str] = None, 
                      output_filename: Optional[str] = None) -> str:
        # Input validation
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text cannot be empty")
        if len(text) > 5000:
            raise ValueError("Text too long (max 5000 characters)")
        
        voice_id = voice_id or self.default_voice_id
        model = model or self.default_model
        
        if quality_preset:
            voice_settings = self.apply_quality_preset(quality_preset)
        elif voice_settings is None:
            voice_settings = {"stability": 0.5, "similarity_boost": 0.5, "style": 0.0, "use_speaker_boost": True}
        
        self._validate_voice_settings(voice_settings)
        
        if output_filename is None:
            output_filename = f"speech_{int(time.time())}.{self.audio_format}"
        output_filename = self._sanitize_filename(output_filename)
        if not output_filename.endswith(f'.{self.audio_format}'):
            output_filename += f'.{self.audio_format}'
        
        output_path = self.output_dir / output_filename
        
        data = {"text": text, "model_id": model, "voice_settings": voice_settings}
        
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            # Add output format as query parameter for OGG/OPUS
            if self.audio_format == "ogg":
                url += "?output_format=opus_48000_64"
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed. Please check your API key")
            elif response.status_code == 402:
                raise Exception("Insufficient quota. Please check your account balance")
            elif response.status_code == 422:
                raise ValueError("Invalid request parameters")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please try again later")
            
            response.raise_for_status()
            
            if len(response.content) == 0:
                raise Exception("Received empty audio data")
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise Exception("Audio file was not created successfully")
            
            print(f"Audio saved to: {output_path}")
            return str(output_path)
        
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error. Please check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def get_account_info(self) -> Dict:
        try:
            url = f"{self.base_url}/user"
            headers = {"xi-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get account info: {str(e)}")
    
    def estimate_cost(self, text: str) -> Dict:
        char_count = len(text)
        return {
            "character_count": char_count,
            "estimated_cost_usd": char_count * 0.0003,
            "free_tier_usage": f"{char_count}/10000 characters"
        }


def main():
    parser = argparse.ArgumentParser(
        description='Convert text to speech using ElevenLabs API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "Hello, world!"
  python cli.py "Hello, world!" --voice-id "21m00Tcm4TlvDq8ikWAM"
  python cli.py "Hello, world!" --quality-preset "podcast"
  python cli.py --text-file "input.txt" --output "story.mp3"
  python cli.py --account-info
        """
    )
    
    # Text input options
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument('text', nargs='?', help='Text to convert to speech')
    text_group.add_argument('--text-file', '-f', type=str, help='Path to text file')
    
    # Voice options
    parser.add_argument('--voice-id', '-v', type=str, help='Voice ID')
    
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    parser.add_argument('--model', '-m', type=str, 
                       choices=['eleven_monolingual_v1', 'eleven_multilingual_v2', 'eleven_multilingual_v1'],
                       help='Model to use')
    
    # Voice settings
    parser.add_argument('--quality-preset', '-q', type=str,
                       choices=['podcast', 'audiobook', 'conversational', 'professional', 'expressive', 'news'],
                       help='Audio quality preset')
    parser.add_argument('--list-presets', action='store_true', help='List quality presets')
    parser.add_argument('--stability', type=float, default=0.5, help='Voice stability (0.0-1.0)')
    parser.add_argument('--similarity-boost', type=float, default=0.5, help='Similarity boost (0.0-1.0)')
    parser.add_argument('--style', type=float, default=0.0, help='Voice style (0.0-1.0)')
    
    # Utility options
    parser.add_argument('--account-info', action='store_true', help='Show account info')
    parser.add_argument('--estimate-cost', action='store_true', help='Estimate cost')
    
    args = parser.parse_args()
    
    try:
        tts_service = TextToSpeechService()
        

        if args.list_presets:
            print("Available Quality Presets:")
            print("-" * 40)
            presets = tts_service.get_audio_quality_presets()
            for name, preset in presets.items():
                print(f"Name: {name}")
                print(f"Description: {preset['description']}")
                print(f"Settings: stability={preset['stability']}, similarity_boost={preset['similarity_boost']}")
                print("-" * 30)
            return
        
        if args.account_info:
            print("Account Information:")
            print("-" * 30)
            info = tts_service.get_account_info()
            print(f"User ID: {info.get('user_id', 'N/A')}")
            subscription = info.get('subscription', {})
            print(f"Subscription: {subscription.get('tier', 'N/A')}")
            print(f"Characters: {subscription.get('character_count', 0)}/{subscription.get('character_limit', 0)}")
            return
        
        # Get text input
        text = None
        if args.text:
            text = args.text
        elif args.text_file:
            try:
                with open(args.text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except FileNotFoundError:
                print(f"Error: File '{args.text_file}' not found")
                sys.exit(1)
        else:
            print("Error: Please provide text or use --text-file option")
            parser.print_help()
            sys.exit(1)
        
        if args.estimate_cost:
            cost_info = tts_service.estimate_cost(text)
            print("Cost Estimation:")
            print("-" * 20)
            print(f"Characters: {cost_info['character_count']}")
            print(f"Estimated Cost: ${cost_info['estimated_cost_usd']:.4f}")
            print(f"Free Tier: {cost_info['free_tier_usage']}")
            return
        
        # Determine voice ID
        voice_id = args.voice_id  # Use provided voice ID or None for default
        
        # Prepare voice settings
        voice_settings = None
        if not args.quality_preset:
            voice_settings = {
                "stability": args.stability,
                "similarity_boost": args.similarity_boost,
                "style": args.style,
                "use_speaker_boost": True
            }
        
        # Generate speech
        print("Generating speech...")
        if args.quality_preset:
            print(f"Using quality preset: {args.quality_preset}")
        
        output_path = tts_service.text_to_speech(
            text=text,
            voice_id=voice_id,
            model=args.model,
            voice_settings=voice_settings,
            quality_preset=args.quality_preset,
            output_filename=args.output
        )
        
        print(f"Success! Audio file generated: {output_path}")
        cost_info = tts_service.estimate_cost(text)
        print(f"Characters used: {cost_info['character_count']}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()