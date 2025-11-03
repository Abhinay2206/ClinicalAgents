export default function LoadingSkeleton() {
  return (
    <div className="h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 animate-pulse">
          <div className="w-8 h-8 bg-white rounded-lg"></div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-48 bg-gray-200 dark:bg-gray-700 rounded mx-auto animate-pulse"></div>
          <div className="h-3 w-32 bg-gray-200 dark:bg-gray-700 rounded mx-auto animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
