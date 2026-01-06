import { FileText, X, File, FileJson, FileSpreadsheet } from 'lucide-react';

interface FilePreviewProps {
  files: File[];
  onRemove: (index: number) => void;
  disabled?: boolean;
}

export function FilePreview({ files, onRemove, disabled = false }: FilePreviewProps) {
  if (files.length === 0) return null;

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  };

  const getFileIcon = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();

    switch (ext) {
      case 'json':
        return <FileJson className="w-5 h-5 text-yellow-400" />;
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5 text-green-400" />;
      case 'pdf':
        return <File className="w-5 h-5 text-red-400" />;
      case 'md':
        return <FileText className="w-5 h-5 text-blue-400" />;
      default:
        return <FileText className="w-5 h-5 text-text-secondary" />;
    }
  };

  return (
    <div className="flex flex-wrap gap-2 p-3 bg-bg-primary rounded-lg border border-border">
      {files.map((file, index) => (
        <div
          key={`${file.name}-${index}`}
          className="flex items-center gap-2 px-3 py-2 bg-bg-secondary rounded-lg border border-border group"
        >
          {getFileIcon(file)}

          <div className="flex flex-col min-w-0">
            <span className="text-sm text-text-primary truncate max-w-[150px]">
              {file.name}
            </span>
            <span className="text-xs text-text-secondary">
              {formatFileSize(file.size)}
            </span>
          </div>

          <button
            onClick={() => onRemove(index)}
            disabled={disabled}
            className={`
              p-1 rounded-full
              text-text-secondary hover:text-red-400 hover:bg-red-500/10
              transition-colors
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            title="Retirer le fichier"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
