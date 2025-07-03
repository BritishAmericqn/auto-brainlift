#!/usr/bin/env python3
"""
Style Guide Parser
Converts various style guide formats to Cursor Rules format
"""

import json
import yaml
import re
import sys
from pathlib import Path
from datetime import datetime

class StyleGuideParser:
    def __init__(self, is_merged=False):
        self.supported_formats = ['.md', '.json', '.yaml', '.yml', '.txt']
        # Higher limit for merged files
        self.rule_limit = 150 if is_merged else 50
    
    def parse_file(self, file_path, content):
        """Parse style guide file and convert to Cursor rules"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.json':
            return self.parse_json(content)
        elif ext in ['.yaml', '.yml']:
            return self.parse_yaml(content)
        elif ext == '.md':
            return self.parse_markdown(content)
        else:
            return self.parse_text(content)
    
    def parse_json(self, content):
        """Parse JSON style guide (ESLint, Prettier, etc.)"""
        try:
            config = json.loads(content)
            rules = []
            
            # ESLint rules
            if 'rules' in config:
                rules.append("## ESLint Rules")
                for rule, setting in config['rules'].items():
                    if setting != 'off' and setting != 0:
                        if isinstance(setting, list):
                            rules.append(f"- {rule}: {setting[0]} ({', '.join(map(str, setting[1:]))})")
                        else:
                            rules.append(f"- {rule}: {setting}")
            
            # Prettier rules
            prettier_keys = ['printWidth', 'tabWidth', 'useTabs', 'semi', 'singleQuote', 
                            'trailingComma', 'bracketSpacing', 'arrowParens', 'endOfLine']
            prettier_rules = []
            for key in prettier_keys:
                if key in config:
                    prettier_rules.append(f"- {key}: {config[key]}")
            
            if prettier_rules:
                rules.append("\n## Prettier Configuration")
                rules.extend(prettier_rules)
            
            # Other configurations
            other_rules = []
            for key, value in config.items():
                if key not in ['rules', 'extends', 'plugins', 'parserOptions', 'env'] + prettier_keys:
                    if isinstance(value, (str, int, bool)):
                        other_rules.append(f"- {key}: {value}")
            
            if other_rules:
                rules.append("\n## Additional Configuration")
                rules.extend(other_rules[:20])  # Reasonable limit for additional rules
            
            return self.format_cursor_rules(rules, "JSON Configuration")
            
        except json.JSONDecodeError:
            return self.parse_text(content)
    
    def parse_markdown(self, content):
        """Parse Markdown style guide"""
        rules = []
        
        # Extract headings that suggest rules/guidelines
        rule_headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        for heading in rule_headings:
            if any(keyword in heading.lower() for keyword in ['rule', 'guideline', 'convention', 'standard', 'style', 'format']):
                rules.append(f"\n## {heading}")
                
                # Try to extract content after this heading
                heading_pattern = re.escape(heading)
                section_match = re.search(rf'^#+\s+{heading_pattern}\s*\n(.*?)(?=^#|\Z)', content, re.MULTILINE | re.DOTALL)
                if section_match:
                    section_content = section_match.group(1).strip()
                    # Extract bullet points from this section
                    bullets = re.findall(r'^\s*[-*+]\s+(.+)$', section_content, re.MULTILINE)
                    bullets_to_add = bullets[:15] if self.rule_limit > 50 else bullets[:10]
                    rules.extend([f"- {bullet}" for bullet in bullets_to_add])
        
        # Extract code blocks with descriptions
        code_examples = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        if code_examples and len(rules) < self.rule_limit - 10:
            rules.append("\n## Code Examples")
            rules.append("- Follow the coding patterns demonstrated in the style guide")
        
        # If we didn't find many rules, try extracting any bullet points
        if len(rules) < 10:
            all_bullets = re.findall(r'^\s*[-*+]\s+(.+)$', content, re.MULTILINE)
            for bullet in all_bullets:
                if len(bullet) > 10 and len(bullet) < 200:  # Reasonable length
                    rules.append(f"- {bullet}")
                if len(rules) >= self.rule_limit:  # Stop if we hit the limit
                    break
        
        return self.format_cursor_rules(rules, "Markdown Style Guide")
    
    def parse_yaml(self, content):
        """Parse YAML configuration"""
        try:
            config = yaml.safe_load(content)
            rules = self.extract_rules_from_dict(config)
            return self.format_cursor_rules(rules, "YAML Configuration")
        except yaml.YAMLError:
            return self.parse_text(content)
    
    def parse_text(self, content):
        """Parse plain text style guide"""
        lines = content.split('\n')
        rules = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                # Look for lines that appear to be rules
                if any(indicator in line for indicator in [':', '-', '*', '•', '→', '=>']):
                    if line.startswith(('-', '*', '•')):
                        rules.append(line)
                    else:
                        rules.append(f"- {line}")
            
            if len(rules) >= self.rule_limit:
                break
        
        return self.format_cursor_rules(rules, "Text Style Guide")
    
    def extract_rules_from_dict(self, obj, prefix=""):
        """Recursively extract rules from dictionary"""
        rules = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, dict):
                    nested_rules = self.extract_rules_from_dict(value, f"{prefix}{key}.")
                    if len(rules) + len(nested_rules) < self.rule_limit:
                        rules.extend(nested_rules)
                elif isinstance(value, list) and len(value) < 5:
                    rules.append(f"- {prefix}{key}: {', '.join(map(str, value))}")
                elif isinstance(value, (str, int, bool, float)):
                    rules.append(f"- {prefix}{key}: {value}")
        
        return rules[:self.rule_limit]
    
    def format_cursor_rules(self, rules, source_type):
        """Format rules into Cursor-compatible format"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add note if merged files exceeded normal limit
        merge_note = ""
        if self.rule_limit > 50 and len(rules) > 50:
            merge_note = "\n\n*Note: This style guide was created by merging multiple files to accommodate comprehensive coding standards.*"
        
        cursor_rules = f"""---
description: Auto-Brainlift Style Guide ({source_type})
alwaysApply: true
---

# Project Style Guide

This style guide has been automatically converted from your uploaded configuration.
Follow these conventions when writing or modifying code in this project.{merge_note}

## Coding Standards

{chr(10).join(rules) if rules else "No specific rules extracted. Please review the original style guide."}

## AI Assistant Instructions

When helping with this project:
1. Always follow the above style guidelines
2. Apply these rules to any code suggestions
3. Maintain consistency with existing code patterns
4. Highlight any deviations from these standards
5. Prioritize readability and maintainability

## Auto-Generated Notice

This file was generated by Auto-Brainlift from your uploaded style guide.
To update these rules, upload a new style guide file in the Auto-Brainlift settings.

Last updated: {timestamp}
"""
        return cursor_rules

def main():
    """Main entry point for command-line usage"""
    if len(sys.argv) < 3:
        print("Usage: python style_guide_parser.py <file_path> <output_path> [--merged]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = sys.argv[2]
    is_merged = '--merged' in sys.argv
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse and convert
        parser = StyleGuideParser(is_merged=is_merged)
        result = parser.parse_file(file_path, content)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"Successfully converted {file_path} to Cursor rules")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 