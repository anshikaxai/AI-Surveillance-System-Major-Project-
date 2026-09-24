import {
  Video,
  Radio,
  Cpu,
  Users,
  Car,
} from 'lucide-react';

export default function LiveFeed() {

  const streamUrl =
    '/api/live-feed/demo';

  return (
    <div className="card overflow-hidden animate-slide_in">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-base-600/40">

        <div className="flex items-center gap-3">

          <div className="w-9 h-9 rounded-xl bg-accent-green/10 border border-accent-green/20 flex items-center justify-center">

            <Video
              size={18}
              className="text-accent-green"
            />

          </div>

        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">

          <span className="relative flex h-2.5 w-2.5">

            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />

            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />

          </span>

          LIVE

        </div>

      </div>


      {/* Stream */}
      <div className="relative bg-black aspect-video overflow-hidden">

        <img
          src={streamUrl}
          alt="AI Surveillance Camera Feed"
          className="w-full h-full object-contain"
        />


        {/* top left camera badge */}

      

        {/* bottom overlay */}

        <div className="absolute left-4 right-4 bottom-4 flex items-end justify-between gap-3">

          <div className="flex gap-2">

            <div className="bg-black/70 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2">

              <div className="flex items-center gap-1.5">

                <Cpu
                  size={12}
                  className="text-accent-green"
                />

                <span className="text-[10px] text-accent-green font-semibold">
                  AI ACTIVE
                </span>

              </div>

            </div>

            <div className="bg-black/70 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2">

              <div className="flex items-center gap-1.5">

                <Users size={12} />

                <span className="text-[10px] text-white/80">
                  Person Detection
                </span>

              </div>

            </div>

            <div className="bg-black/70 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2">

              <div className="flex items-center gap-1.5">

                <Car size={12} />

                <span className="text-[10px] text-white/80">
                  Vehicle Detection
                </span>

              </div>

            </div>

          </div>


          <div className="hidden sm:block bg-black/70 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2">

            <span className="text-[9px] text-white/50">
              YOLOv8 · Real-time processing
            </span>

          </div>

        </div>

      </div>

    </div>
  );
}