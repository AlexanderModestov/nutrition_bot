import json
import os
import logging
import anthropic
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
import PyPDF2

logger = logging.getLogger(__name__)

def get_claude_response(client: anthropic.Anthropic, text: str, system_prompt: str, user_prompt: str) -> str:
    """Helper function to get response from Claude API"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"{user_prompt}\n\n{text}"}
            ]
        )
        # Extract the text content from the message
        response_text = message.content[0].text if isinstance(message.content, list) else message.content
        return str(response_text)
    except Exception as e:
        logger.error(f"Error getting Claude response: {e}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise

def process_text_file(file_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Process a single text or PDF file to generate video metadata using Claude API.

    Args:
        file_path: Path to the text or PDF file
        api_key: Optional Claude API key (will use env var if not provided)

    Returns:
        Dictionary containing video metadata (name, descriptions)
    """
    try:
        # Get API key with better error handling
        api_key = api_key or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")

        # Initialize Claude client with the API key
        client = anthropic.Anthropic(api_key=api_key)

        # Read file content based on file type
        if file_path.endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        
        # Get video name from content
        name = get_claude_response(
            client,
            content,
            "Вы профессиональный контент-анализатор. Придумайте четкое, краткое название.",
            "Основываясь на этом контенте, предложите подходящее название для видео (макс. 5 слов). В качестве результаты оставь только предлагаемое название"
        )
        
        # Get short description
        short_desc = get_claude_response(
            client,
            content,
            "Вы профессиональный автор контента. Создайте краткое описание в формате характеристик и ключевых моментов.",
            "Создайте краткое описание (1-2 предложения) основных идей и практической пользы этого контента. Пишите в стиле аннотации, перечисляя ключевые темы и выводы. Не используйте форму пересказа от третьего лица. В качестве результата оставь только описание"
        )

        # Get long description
        long_desc = get_claude_response(
            client,
            content,
            "Вы профессиональный автор контента. Создайте информативное описание в формате структурированного резюме.",
            "Создайте подробное описание (3-5 предложений), перечисляя основные темы, обсуждаемые вопросы и ключевые выводы. Пишите как аннотацию или резюме материала, описывая содержание через перечисление тем и идей. Не пересказывайте от третьего лица. В качестве результата оставь только описание"
        )
        
        # Create metadata dictionary
        metadata = {
            "name": name.strip(),
            "short_description": short_desc.strip(),
            "long_description": long_desc.strip(),
            "file_name": Path(file_path).stem
        }
        
        logger.info(f"Successfully processed {file_path}")
        return metadata
        
    except ValueError as ve:
        logger.error(f"API Key Error: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise

def save_video_descriptions(metadata: Dict, output_path: str):
    """Save video metadata to JSON file"""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create or update JSON structure
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
        else:
            json_content = {"videos": {}}
        
        # Add or update video entry
        json_content["videos"][metadata["file_name"]] = {
            "name": metadata["name"],
            "short_description": metadata["short_description"],
            "long_description": metadata["long_description"]
        }
        
        # Save updated JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Successfully saved metadata to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
        return False

def process_single_file(file_path: str, output_path: str = "configs/video_descriptions.json"):
    """
    Process a single text file and save its metadata.
    
    Args:
        file_path: Path to the text file to process
        output_path: Path where to save the JSON file (default: configs/video_descriptions.json)
    """
    try:
        # Process file and get metadata
        metadata = process_text_file(file_path)
        
        # Save metadata
        if metadata:
            success = save_video_descriptions(metadata, output_path)
            if success:
                print(f"Successfully processed and saved metadata for {file_path}")
                return True
            else:
                print(f"Failed to save metadata for {file_path}")
        return False
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return False

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check for API key before processing
    if not os.getenv('CLAUDE_API_KEY'):
        logger.error("CLAUDE_API_KEY not found in environment variables")
        return
    
    # Get the project root directory and set up paths
    project_root = Path(__file__).parent.parent.parent
    input_dir = project_root / 'data' / 'pdf'
    output_path = project_root / 'configs' / 'pdf_descriptions.json'

    # Check if directory is empty
    if not os.listdir(input_dir):
        logger.warning(f"No files found in {input_dir}")
        return

    # Process all .txt and .pdf files in the directory
    successful = 0
    failed = 0

    for file_name in os.listdir(input_dir):
        if file_name.endswith(('.txt', '.pdf')):
            file_path = input_dir / file_name
            logger.info(f"Processing file: {file_name}")

            if process_single_file(str(file_path), str(output_path)):
                successful += 1
            else:
                failed += 1
    
    # Print summary
    logger.info(f"Processing complete. Successfully processed: {successful}, Failed: {failed}")

if __name__ == "__main__":
    main()
