import { inputClass } from "./FormField";

export function Textarea({
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea className={`${inputClass} min-h-[88px] resize-y ${className}`} {...props} />
  );
}
