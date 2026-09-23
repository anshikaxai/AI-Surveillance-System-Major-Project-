import ROIManager from '../components/ROIManager';

export default function ROIsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-white">ROI Management</h1>
        <p className="text-sm text-white/50 mt-1">
          Spatial zones that feed the Event Intelligence Layer. Polygons, loitering thresholds, crowd limits, active hours.
        </p>
      </div>
      <ROIManager />
    </div>
  );
}
