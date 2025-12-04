export default function Loading() {
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#00B4F0] border-t-transparent" />
        <p className="text-sm font-medium text-[#00283F]">
          Carregando...
        </p>
      </div>
    </div>
  );
}
