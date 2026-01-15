"""Constants for codesynth."""

from typing import List, Set

# Binary file detection via magic bytes (first bytes of common binary formats)
BINARY_SIGNATURES: List[bytes] = [
    b"\x89PNG",  # PNG
    b"\xff\xd8\xff",  # JPEG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"PK\x03\x04",  # ZIP, DOCX, XLSX, JAR, APK
    b"PK\x05\x06",  # ZIP empty
    b"\x50\x4b\x07\x08",  # ZIP spanned
    b"%PDF",  # PDF
    b"\x7fELF",  # ELF executable
    b"MZ",  # Windows executable
    b"\xca\xfe\xba\xbe",  # Java class / Mach-O fat binary
    b"\xfe\xed\xfa\xce",  # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit
    b"\xcf\xfa\xed\xfe",  # Mach-O 64-bit reversed
    b"\x1f\x8b",  # GZIP
    b"BZ",  # BZIP2
    b"\xfd7zXZ",  # XZ
    b"Rar!\x1a\x07",  # RAR
    b"\x00\x00\x00\x1c\x66\x74\x79\x70",  # MP4/M4A
    b"\x00\x00\x00\x20\x66\x74\x79\x70",  # MP4
    b"ID3",  # MP3 with ID3
    b"\xff\xfb",  # MP3
    b"\xff\xfa",  # MP3
    b"OggS",  # OGG
    b"RIFF",  # WAV, AVI
    b"fLaC",  # FLAC
    b"\x00\x00\x01\x00",  # ICO
    b"OTTO",  # OpenType font
    b"\x00\x01\x00\x00",  # TrueType font
    b"wOFF",  # WOFF
    b"wOF2",  # WOFF2
    b"\x1a\x45\xdf\xa3",  # WebM/MKV
    b"SQLite format 3",  # SQLite
    b"\x00asm",  # WebAssembly
]

# Known binary file extensions (lowercase, without dot)
BINARY_EXTENSIONS: Set[str] = {
    # Images
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "ico",
    "webp",
    "svg",
    "tiff",
    "tif",
    "psd",
    "raw",
    "heic",
    "heif",
    "avif",
    # Audio
    "mp3",
    "wav",
    "flac",
    "aac",
    "ogg",
    "wma",
    "m4a",
    "opus",
    # Video
    "mp4",
    "avi",
    "mkv",
    "mov",
    "wmv",
    "flv",
    "webm",
    "m4v",
    "mpeg",
    "mpg",
    # Archives
    "zip",
    "tar",
    "gz",
    "rar",
    "7z",
    "bz2",
    "xz",
    "iso",
    "dmg",
    # Executables & Libraries
    "exe",
    "dll",
    "so",
    "dylib",
    "bin",
    "out",
    "app",
    "msi",
    # Documents (binary)
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    # Fonts
    "ttf",
    "otf",
    "woff",
    "woff2",
    "eot",
    # Database
    "db",
    "sqlite",
    "sqlite3",
    "mdb",
    # Other
    "pyc",
    "pyo",
    "class",
    "jar",
    "war",
    "ear",
    "apk",
    "ipa",
    "o",
    "a",
    "lib",
    "obj",
    "wasm",
}

# Extension to language mapping for syntax highlighting
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "rb": "ruby",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "kt": "kotlin",
    "swift": "swift",
    "c": "c",
    "cpp": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "h": "c",
    "hpp": "cpp",
    "cs": "csharp",
    "php": "php",
    "sh": "bash",
    "bash": "bash",
    "zsh": "zsh",
    "fish": "fish",
    "ps1": "powershell",
    "sql": "sql",
    "html": "html",
    "htm": "html",
    "css": "css",
    "scss": "scss",
    "sass": "sass",
    "less": "less",
    "json": "json",
    "xml": "xml",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "cfg": "ini",
    "conf": "ini",
    "md": "markdown",
    "markdown": "markdown",
    "rst": "rst",
    "tex": "latex",
    "r": "r",
    "R": "r",
    "m": "matlab",
    "lua": "lua",
    "pl": "perl",
    "pm": "perl",
    "ex": "elixir",
    "exs": "elixir",
    "erl": "erlang",
    "hrl": "erlang",
    "clj": "clojure",
    "cljs": "clojure",
    "scala": "scala",
    "hs": "haskell",
    "ml": "ocaml",
    "fs": "fsharp",
    "vim": "vim",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "cmake": "cmake",
    "groovy": "groovy",
    "gradle": "groovy",
    "tf": "hcl",
    "hcl": "hcl",
    "proto": "protobuf",
    "graphql": "graphql",
    "gql": "graphql",
    "vue": "vue",
    "svelte": "svelte",
}

# Common source code directories to auto-detect (in priority order)
COMMON_SOURCE_DIRS: List[str] = [
    "src",
    "lib",
    "app",
    "source",
    "code",
    "pkg",
    "packages",
    "modules",
    "core",
    "internal",
    "cmd",  # Go projects
    "backend",
    "frontend",
    "server",
    "client",
    "api",
    "services",
    "components",
]

# Default directories to always ignore
DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".env",
}
