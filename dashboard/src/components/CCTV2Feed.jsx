import {
  Users,
  Activity,
  ShieldAlert,
  Clock3,
} from 'lucide-react';

export default function CCTV2Feed() {
  return (
    <div className="card overflow-hidden">

      <div className="flex items-center justify-between px-5 py-4 border-b border-base-600/40">

        <div>
          <h3 className="text-white font-semibold">
            CCTV 2 — Human Activity
          </h3>

          <p className="text-xs text-white/40 mt-1">
            University Lobby · CAM-002
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-400 font-semibold">

          <span className="relative flex h-2.5 w-2.5">

            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />

            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />

          </span>

          LIVE

        </div>

      </div>


      <div className="relative bg-black aspect-video">

        <img
          src="/api/live-feed/cctv2"
          alt="CCTV 2 Human Activity Feed"
          className="w-full h-full object-contain"
        />


        <div className="absolute left-4 bottom-7 flex flex-wrap gap-2">

          <div className="bg-black/70 border border-white/10 rounded-lg px-3 py-2 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <Users
                size={12}
                className="text-emerald-400"
              />

              <span className="text-[10px] text-white">
                Person Tracking
              </span>
            </div>
          </div>


          <div className="bg-black/70 border border-white/10 rounded-lg px-3 py-2 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <Activity
                size={12}
                className="text-yellow-400"
              />

              <span className="text-[10px] text-white">
                Behaviour
              </span>
            </div>
          </div>


          <div className="bg-black/70 border border-white/10 rounded-lg px-3 py-2 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <Clock3
                size={12}
                className="text-orange-400"
              />

              <span className="text-[10px] text-white">
                Loitering
              </span>
            </div>
          </div>


          <div className="bg-black/70 border border-white/10 rounded-lg px-3 py-2 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <ShieldAlert
                size={12}
                className="text-red-400"
              />

              <span className="text-[10px] text-white">
                Restricted Zone
              </span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}   