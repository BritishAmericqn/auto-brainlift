# Test Style Guides for Auto-Brainlift

This directory contains various style guide formats to test the Style Guide Integration feature in Auto-Brainlift.

## Available Test Files

### 1. **eslint-config.json**
A comprehensive ESLint configuration with TypeScript support and detailed rules for code quality.

### 2. **prettier-config.json**
A Prettier configuration file defining code formatting preferences like indentation, quotes, and line length.

### 3. **javascript-style-guide.md**
A detailed Markdown style guide covering:
- Naming conventions
- Code formatting rules
- Best practices
- Error handling
- Documentation standards
- Testing guidelines

### 4. **team-standards.yaml**
A YAML configuration file containing comprehensive team development standards including:
- Code style preferences
- Architecture guidelines
- Git workflow rules
- Performance requirements
- Security standards

### 5. **simple-rules.txt**
A plain text file with straightforward coding rules and guidelines, demonstrating that even simple text files can be parsed.

### 6. **.eslintrc.json**
A combined ESLint and Prettier configuration that many teams use, showing how the parser handles integrated configs.

### 7. **teamstyle_1.txt, teamstyle_2.txt, teamstyle_3.txt**
A three-part comprehensive team coding standard for testing multi-file merging:
- Demonstrates automatic file merging when files share the same prefix
- Shows how 120+ rules can be captured (exceeding single-file limit)
- Tests numeric ordering of file parts

### 8. **oldstyle.json**
A sample file to test cleanup behavior - should be deleted when uploading teamstyle files.

### 9. **teamstyle_OLD.txt**  
Tests cleanup of invalid suffixes - has correct prefix but non-numeric suffix, should be deleted.

## How to Test

1. **Start Auto-Brainlift**
   ```bash
   npm start
   ```

2. **Open Settings**
   - Click the settings button in the UI
   - Navigate to the "Style Guide Integration" section

3. **Enable Style Guide**
   - Toggle "Enable project-specific style guide" to ON
   - The file upload section will appear

4. **Upload a Test File**
   - Click "Browse Files"
   - Navigate to the `test-style-guides` directory
   - Select any of the test files
   - The file will be uploaded and processed

5. **Review the Preview**
   - After upload, a preview of the generated Cursor Rules will appear
   - This shows how your style guide has been converted

6. **Verify Files Created**
   - Check your project directory for `.auto-brainlift/style-guide/`
   - You should see:
     - Your uploaded file
     - A generated `cursor-rules.md` file

## Expected Results

Each file type should produce a properly formatted Cursor Rules file with:

- **Header metadata** indicating it's an Auto-Brainlift style guide
- **Coding Standards section** with extracted rules
- **AI Assistant Instructions** for Cursor to follow
- **Auto-generated notice** with timestamp

## Testing Different Scenarios

### Success Cases
- ✅ All file types (.json, .md, .yaml, .yml, .txt) should upload successfully
- ✅ Files under 1MB should process without issues
- ✅ Preview should show formatted rules
- ✅ Settings should persist after closing/reopening

### Error Cases to Test
- ❌ Files over 1MB should show "File too large" error
- ❌ Unsupported file types (e.g., .pdf, .doc) should be rejected
- ❌ Corrupted JSON/YAML should still save but show parse error

## Checking Integration

After uploading a style guide:

1. The generated rules are saved to `.auto-brainlift/style-guide/cursor-rules.md`
2. Project settings are updated with style guide information
3. The file can be manually copied to `.cursor/rules/` for Cursor integration
4. Future versions will automate this integration

## Multi-File Style Guides

For comprehensive style guides that exceed 50 rules, you can split them into multiple numbered files:

### **teamstyle_1.txt, teamstyle_2.txt, teamstyle_3.txt**
A three-part comprehensive team coding standard demonstrating:
- Part 1: General principles and philosophy
- Part 2: JavaScript/TypeScript specifics  
- Part 3: Workflow and tooling

**How it works:**
1. Upload any file in the sequence (e.g., `teamstyle_2.txt`)
2. Auto-Brainlift automatically:
   - Finds all files with the same prefix (`teamstyle_`)
   - Merges them in numeric order (1, 2, 3)
   - Generates a unified Cursor Rules file with up to 150 rules
   - Deletes any old style guides with different prefixes

### Advanced Features

**Permanent Style Guides:**
- Check "Mark as permanent" when uploading
- Permanent files won't be deleted when uploading new style guides
- Useful for keeping reference standards alongside project-specific rules
- Requires manual file system navigation to remove

**Automatic Cleanup:**
- Uploading `mystyle_1.txt` deletes previous `teamguide.json`
- Files with same prefix but invalid suffixes are removed (e.g., `mystyle_OLD.txt`)
- Only numbered sequences are preserved (`mystyle_1`, `mystyle_2`, not `mystyle1`)

## Tips for Testing

- Try uploading different file types in sequence
- Test the toggle on/off behavior
- Upload a file, close settings, reopen to verify persistence
- Check that each project maintains its own style guide
- Verify that the preview accurately reflects the parsed rules
- Test multi-file merging with the `teamstyle_` files
- Try the permanent flag to protect important style guides
- Verify cleanup behavior when switching between different style guide sets 