import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  width = '100%', 
  height = '1rem', 
  borderRadius = '4px',
  className = '',
  style = {}
}) => {
  return (
    <div 
      className={`skeleton-loader ${className}`}
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        backgroundImage: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.03), transparent)',
        backgroundSize: '200% 100%',
        animation: 'skeleton-shimmer 1.5s infinite linear',
        ...style
      }}
    />
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="brutal-card skeleton-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ width: '60%' }}>
          <Skeleton height="1.5rem" width="80%" style={{ marginBottom: '0.5rem' }} />
          <Skeleton height="0.8rem" width="60%" />
        </div>
        <Skeleton width="40px" height="24px" />
      </div>
      <div style={{ marginTop: '2rem' }}>
        <Skeleton height="0.8rem" width="30%" style={{ marginBottom: '1rem' }} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <Skeleton height="4rem" />
          <Skeleton height="4rem" />
        </div>
      </div>
      <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
        <Skeleton width="40%" height="0.8rem" />
        <Skeleton width="20%" height="0.8rem" />
      </div>
    </div>
  );
};

export const DashboardSkeleton: React.FC = () => {
  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <header style={{ marginBottom: '3rem' }}>
        <Skeleton height="3.5rem" width="30%" style={{ marginBottom: '1rem' }} />
        <Skeleton height="1.2rem" width="50%" />
      </header>
      
      <div className="brutal-card glass" style={{ marginBottom: '3rem', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Skeleton height="0.8rem" width="20%" style={{ marginBottom: '1rem' }} />
        <Skeleton height="4rem" width="40%" style={{ marginBottom: '1rem' }} />
        <div style={{ display: 'flex', gap: '2rem' }}>
          <Skeleton width="80px" height="1.2rem" />
          <Skeleton width="120px" height="1.2rem" />
        </div>
      </div>

      <div className="dashboard-grid">
        {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
      </div>
    </div>
  );
};
