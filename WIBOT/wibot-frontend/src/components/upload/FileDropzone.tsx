import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'text/csv': ['.csv'],
  'application/json': ['.json'],
};

const MAX_FILE_SIZE = parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '10485760', 10); // 10MB

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export function FileDropzone({ onFilesSelected, disabled = false }: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFilesSelected(acceptedFiles);
      }
    },
    [onFilesSelected]
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    fileRejections,
  } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    disabled,
    multiple: true,
  });

  const hasErrors = fileRejections.length > 0;

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-6
          transition-colors cursor-pointer
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${isDragActive && !isDragReject ? 'border-accent bg-accent/10' : ''}
          ${isDragReject ? 'border-red-500 bg-red-500/10' : ''}
          ${!isDragActive && !isDragReject ? 'border-border hover:border-accent/50 hover:bg-bg-primary/50' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-3 text-center">
          {isDragReject ? (
            <>
              <AlertCircle className="w-10 h-10 text-red-400" />
              <div>
                <p className="text-red-400 font-medium">Fichier non accepté</p>
                <p className="text-xs text-text-secondary mt-1">
                  Formats acceptés : PDF, TXT, MD, CSV, JSON
                </p>
              </div>
            </>
          ) : isDragActive ? (
            <>
              <Upload className="w-10 h-10 text-accent" />
              <p className="text-accent font-medium">Déposez les fichiers ici</p>
            </>
          ) : (
            <>
              <FileText className="w-10 h-10 text-text-secondary" />
              <div>
                <p className="text-text-primary font-medium">
                  Glissez-déposez vos fichiers ici
                </p>
                <p className="text-sm text-text-secondary mt-1">
                  ou cliquez pour sélectionner
                </p>
                <p className="text-xs text-text-secondary mt-2">
                  PDF, TXT, MD, CSV, JSON (max 10 Mo)
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Error messages */}
      {hasErrors && (
        <div className="space-y-1">
          {fileRejections.map(({ file, errors }) => (
            <div
              key={file.name}
              className="flex items-start gap-2 text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2"
            >
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium">{file.name}</span>
                <ul className="text-xs mt-0.5">
                  {errors.map((error) => (
                    <li key={error.code}>
                      {error.code === 'file-too-large'
                        ? 'Fichier trop volumineux (max 10 Mo)'
                        : error.code === 'file-invalid-type'
                        ? 'Type de fichier non accepté'
                        : error.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
