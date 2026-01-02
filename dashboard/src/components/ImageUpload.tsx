import { useState, useRef, useCallback } from 'react';
import type { ImageRef } from '../types/api';

interface ImageUploadProps {
  onImagesSelected: (files: File[]) => void;
  onImageRemove: (index: number) => void;
  pendingImages: File[];
  uploadedImages: ImageRef[];
  maxImages?: number;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];

export default function ImageUpload({
  onImagesSelected,
  onImageRemove,
  pendingImages,
  uploadedImages,
  maxImages = 5,
  disabled = false,
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const totalImages = pendingImages.length + uploadedImages.length;
  const canAddMore = totalImages < maxImages;

  const validateFiles = useCallback((files: FileList | File[]): File[] => {
    const validFiles: File[] = [];
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        setError(`${file.name}: Invalid file type. Use PNG, JPEG, GIF, or WebP.`);
        continue;
      }
      if (file.size > MAX_FILE_SIZE) {
        setError(`${file.name}: File too large. Max 10MB.`);
        continue;
      }
      if (totalImages + validFiles.length >= maxImages) {
        setError(`Maximum ${maxImages} images allowed.`);
        break;
      }
      validFiles.push(file);
    }

    return validFiles;
  }, [totalImages, maxImages]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files.length > 0) {
      const validFiles = validateFiles(e.target.files);
      if (validFiles.length > 0) {
        onImagesSelected(validFiles);
      }
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [validateFiles, onImagesSelected]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);

    if (disabled || !canAddMore) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const validFiles = validateFiles(files);
      if (validFiles.length > 0) {
        onImagesSelected(validFiles);
      }
    }
  }, [disabled, canAddMore, validateFiles, onImagesSelected]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && canAddMore) {
      setIsDragging(true);
    }
  }, [disabled, canAddMore]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  return (
    <div className="space-y-2">
      {(pendingImages.length > 0 || uploadedImages.length > 0) && (
        <div className="flex flex-wrap gap-2">
          {pendingImages.map((file, index) => (
            <div key={`pending-${index}`} className="relative group">
              <img
                src={URL.createObjectURL(file)}
                alt={file.name}
                className="w-16 h-16 object-cover rounded border border-gray-600"
              />
              <button
                type="button"
                onClick={() => onImageRemove(index)}
                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                disabled={disabled}
              >
                ×
              </button>
              <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-xs text-center text-gray-300 truncate px-1">
                {(file.size / 1024).toFixed(0)}KB
              </div>
            </div>
          ))}
        </div>
      )}

      {canAddMore && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-3 text-center transition-colors cursor-pointer
            ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          onClick={() => !disabled && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_TYPES.join(',')}
            multiple
            onChange={handleFileSelect}
            className="hidden"
            disabled={disabled}
          />
          <div className="text-gray-400 text-sm">
            <span className="text-blue-400">Click to upload</span> or drag and drop
            <div className="text-xs text-gray-500 mt-1">
              PNG, JPG, GIF, WebP up to 10MB ({totalImages}/{maxImages})
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-400 text-xs">{error}</div>
      )}
    </div>
  );
}
