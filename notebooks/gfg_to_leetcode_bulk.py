import sys
sys.path.append('.')

from app.search import search_similar_problems
from app.reasoning import generate_reasoning

import faiss
import json
import pandas as pd
from pathlib import Path
import time

# Load index and dataframe
print("Loading LeetCode index and data...")
index = faiss.read_index("./data-local/leetcode.index")
df = pd.read_csv("./data-local/leetcode_clean.csv")
print(f"✓ Loaded {len(df)} problems from index\n")


def search_leetcode_equivalent(problem_statement):
    """
    Search for equivalent LeetCode problem with error handling.
    
    Returns:
        dict: Contains 'success', 'result', 'error' keys
    """
    try:
        normalized_problem, distances, indices = search_similar_problems(problem_statement, index)
        reasoning_result = generate_reasoning(problem_statement, normalized_problem, df, indices)
        
        # Success check: leetcode_title should be non-empty (consistent with main.py)
        if reasoning_result.get('leetcode_title'):
            return {
                'success': True,
                'result': reasoning_result,
                'error': None
            }
        else:
            return {
                'success': False,
                'result': None,
                'error': 'No valid LeetCode match found'
            }
    except Exception as e:
        error_msg = f"Error: {type(e).__name__} - {str(e)}"
        print(f"    ✗ {error_msg}")
        return {
            'success': False,
            'result': None,
            'error': error_msg
        }


def bulk_run(input_file, output_file):
    """
    Process bulk GFG links and map them to LeetCode equivalents.
    
    Counts success/failure rates and confidence level distribution.
    """
    print(f"📂 Reading input file: {input_file}")
    
    # Load scraped links
    with open(input_file, 'r', encoding='utf-8') as f:
        scraped_links = json.load(f)
    
    print(f"✓ Loaded {len(scraped_links)} entries\n")
    
    # Initialize counters
    total_problems = 0
    success_count = 0
    failure_count = 0
    confidence_counts = {
        'Strong match': 0,
        'Moderate match': 0,
        'Weak match': 0
    }
    
    results = []
    
    print("🔄 Processing problems...\n")
    for entry_idx, entry in enumerate(scraped_links, 1):
        title = entry.get('title', 'Unknown')
        module = entry.get('module', '')
        segment = entry.get('segment', '')
        location = f"Module {module}, Segment {segment}" if module and segment else ""
        print(f"[{entry_idx}/{len(scraped_links)}] Processing: {title} {location}")
        
        mapped_links = []
        gfg_problems = entry.get('scraped_gfg_links', [])
        print(f"  → Found {len(gfg_problems)} problems\n")
        
        for problem_idx, scrape_obj in enumerate(gfg_problems, 1):
            total_problems += 1
            problem_text = scrape_obj.get('text', '')[:80]
            print(f"  [{problem_idx:2d}/{len(gfg_problems):2d}] {problem_text}...")
            
            # Search for equivalent LeetCode problem
            search_result = search_leetcode_equivalent(scrape_obj['text'])
            time.sleep(0.5)
            
            if search_result['success']:
                success_count += 1
                reasoning = search_result['result']
                confidence = reasoning.get('confidence', 'Unknown')
                
                # Track confidence levels
                if confidence in confidence_counts:
                    confidence_counts[confidence] += 1
                
                scrape_obj['mapped_result'] = reasoning
                scrape_obj['mapping_success'] = True
                scrape_obj['mapping_error'] = None
                
                leetcode_title = reasoning.get('leetcode_title', 'N/A')
                print(f"           ✓ {leetcode_title} ({confidence})")
            else:
                failure_count += 1
                scrape_obj['mapped_result'] = None
                scrape_obj['mapping_success'] = False
                scrape_obj['mapping_error'] = search_result['error']
                
                print(f"           ✗ {search_result['error']}")
            
            mapped_links.append(scrape_obj)
        
        entry['mapped_links'] = mapped_links
        results.append(entry)
        print()  # Blank line between entries
    
    # Save results
    print(f"💾 Saving results to: {output_file}")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary statistics
    print("\n" + "="*60)
    print("📊 PROCESSING SUMMARY")
    print("="*60)
    print(f"Total problems processed:     {total_problems}")
    print(f"✓ Successful mappings:        {success_count:4d} ({success_count/total_problems*100:5.1f}%)")
    print(f"✗ Failed mappings:            {failure_count:4d} ({failure_count/total_problems*100:5.1f}%)")
    
    if success_count > 0:
        print("\nConfidence Levels (of successful matches):")
        for level in ['Strong match', 'Moderate match', 'Weak match']:
            count = confidence_counts.get(level, 0)
            if count > 0:
                pct = count / success_count * 100
                print(f"  • {level:20s}: {count:4d} ({pct:5.1f}%)")
    
    print("="*60)
    print(f"✓ Results saved successfully!\n")


if __name__ == "__main__":
    input_path = "./data-local/scraped_links.json"
    output_path = "./data-local/mapped_links.json"
    
    print("="*60)
    print("🚀 GFG to LeetCode Bulk Mapper")
    print("="*60 + "\n")
    
    bulk_run(input_path, output_path)