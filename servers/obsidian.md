# Tools
## search_files
Recursively search for files/directories
Inputs:
path (string): Starting directory
pattern (string): Search pattern
excludePatterns (string[]): Exclude any patterns. Glob formats are supported.
Case-insensitive matching
Returns full paths to matches

## read_file
Read complete contents of a file
Input: path (string)
Reads complete file contents with UTF-8 encoding

## read_multiple_files
Read multiple files simultaneously
Input: paths (string[])
Failed reads won't stop the entire operation

## list_directory
List directory contents with [FILE] or [DIR] prefixes
Input: path (string)
get_file_info
Get detailed file/directory metadata
Input: path (string)
Returns:
Size
Creation time
Modified time
Access time
Type (file/directory)
Permissions

## list_allowed_directories
List all directories the server is allowed to access
No input required
Returns:
Directories that this server can read/write from

