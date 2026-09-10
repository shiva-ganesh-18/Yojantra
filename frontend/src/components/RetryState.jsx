import React from 'react';
import LoadingSkeleton from './LoadingSkeleton';
import ErrorState from './ErrorState';
import EmptyState from './EmptyState';

/**
 * RetryState: Unified container for async data loading, error with retry, and empty states.
 */
export const RetryState = ({
  isLoading,
  error,
  isEmpty,
  onRetry,
  skeletonVariant = 'card',
  skeletonCount = 3,
  emptyTitle,
  emptyDescription,
  emptyActionText,
  onEmptyAction,
  errorTitle,
  errorMessage,
  children,
  className = '',
}) => {
  if (isLoading) {
    return <LoadingSkeleton variant={skeletonVariant} count={skeletonCount} className={className} />;
  }

  if (error) {
    return (
      <ErrorState
        title={errorTitle || 'Connection Error'}
        message={errorMessage || (error.message || 'Unable to retrieve data.')}
        technicalDetails={error.response?.data || error.stack}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        actionText={emptyActionText}
        onAction={onEmptyAction}
        className={className}
      />
    );
  }

  return <>{children}</>;
};

export default RetryState;
