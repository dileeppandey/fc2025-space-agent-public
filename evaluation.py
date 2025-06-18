import weave
from weave import Evaluation
from weave import Dataset
import asyncio
import json
import os
import argparse
from typing import Any, List, Dict

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from objects.models.winston import Winston
from objects.scorers.winston.response_quality_judge import ResponseQualityScorer


def parse_args():
    parser = argparse.ArgumentParser(description='Run Winston evaluation')
    parser.add_argument('--trials', type=int, default=1,
                       help='Number of trials to run (default: 1)')
    parser.add_argument('--first-n', type=int,
                       help='Only evaluate on first N examples')
    parser.add_argument('--ids', type=str, nargs='+',
                       help='Only evaluate on examples with these IDs')
    parser.add_argument('--dataset', type=str, default='objects/datasets/eval_public.jsonl',
                       help='Path to dataset file (default: objects/datasets/eval_public.jsonl)')
    parser.add_argument('--use-finetuned', action='store_true',
                       help='Use finetuned model instead of base model (default: False)')
    return parser.parse_args()

def load_dataset(file_path: str) -> List[Dict]:
    """Load dataset from JSONL file."""
    examples = []
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines
            if not line.strip():
                continue
            try:
                example = json.loads(line.strip())
                # Convert to expected format
                examples.append({
                    'id': len(examples),  # Add sequential ID
                    'input': [{'role': 'user', 'content': example['question']}],
                    'target': example['answer']
                })
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {line.strip()}")
                print(f"Error details: {str(e)}")
                continue
    return examples

def filter_dataset(examples: List[Dict], first_n: int = None, ids: List[str] = None) -> List[Dict]:
    """Filter dataset based on provided criteria."""
    if first_n is not None:
        return examples[:first_n]
    elif ids is not None:
        # Convert ids to integers since they're stored as ints in the dataset
        id_list = [int(id) for id in ids]
        return [ex for ex in examples if ex['id'] in id_list]
    return examples

# Preprocess input for evaluation
@weave.op(name="winston-preprocess_model_input")
def preprocess_model_input(example: Dict[str, str]) -> Dict[str, Any]:
    return {
        'messages': example['input']
    }

async def main():
    # Initialize Weave
    client = weave.init(f'{os.getenv("WEAVE_TEAM")}/{os.getenv("WEAVE_PROJECT")}')

    # Initialize the vector database
    # Parse arguments
    args = parse_args()
    
    # Extract dataset identifier from filename (e.g., "public" from "eval_public.jsonl")
    filename = os.path.basename(args.dataset)
    if filename.startswith('eval_') and filename.endswith('.jsonl'):
        dataset_identifier = filename[5:-6]  # Remove 'eval_' prefix and '.jsonl' suffix
    else:
        dataset_identifier = "unknown"
    
    # Load the dataset
    dataset_name = f"WinstonSpaceAgentDataset{dataset_identifier.capitalize()}"
    if args.first_n:
        dataset_name += f"-first{args.first_n}"
    elif args.ids:
        dataset_name += f"-ids{'_'.join(args.ids)}"
    
    examples = load_dataset(args.dataset)
    filtered_examples = filter_dataset(examples, args.first_n, args.ids)
    dataset = Dataset(name=dataset_name, rows=filtered_examples)

    # instantiate winston with all tools
    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    winston = Winston(
        model_id=model_id,
        use_finetuned=args.use_finetuned
    )

    # Initialize the scorers
    quality_scorer = ResponseQualityScorer(model_id=model_id, column_map={"input": "input", "target": "target"})

    # Extract model ID without version for display name
    model_id_for_display = model_id.split('-v')[0] if '-v' in model_id else model_id

    # Create and run the evaluation
    evaluation = Evaluation(
        name="WinstonSpaceAgentEvaluation",
        dataset=dataset,
        preprocess_model_input=preprocess_model_input,
        scorers=[
            quality_scorer
        ],
        trials=args.trials,
    )

    display_name = f"WinstonSpaceAgent{dataset_identifier.capitalize()}.{model_id_for_display}.{args.trials}"
    if args.first_n:
        display_name += f".first{args.first_n}"
    elif args.ids:
        display_name += f".ids{'_'.join(args.ids)}"

    await evaluation.evaluate(winston, __weave={"display_name": display_name})
    client.finish()

if __name__ == "__main__":
    asyncio.run(main())
    