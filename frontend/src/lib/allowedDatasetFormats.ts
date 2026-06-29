/** Dataset extensions accepted for upload (must match backend ALLOWED_FILE_EXTENSIONS). */
export const ALLOWED_DATASET_EXTENSIONS = [
  "csv",
  "tsv",
  "json",
  "jsonl",
  "ndjson",
  "txt",
  "xml",
  "yaml",
  "yml",
  "log",
  "md",
  "pdf",
  "docx",
  "xlsx",
] as const;

export const ALLOWED_DATASET_ACCEPT = ALLOWED_DATASET_EXTENSIONS.map((ext) => `.${ext}`).join(",");

export const ALLOWED_DATASET_LABEL = ALLOWED_DATASET_EXTENSIONS.map((ext) =>
  ext.toUpperCase()
).join(" · ");
