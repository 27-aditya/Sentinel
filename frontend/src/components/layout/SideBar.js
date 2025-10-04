import Image from "next/image";
  
export default function Sidebar(){ 
    return( 
        <div className="hidden md:flex w-[8%] bg-gray-50 flex-col items-center py-6 gap-8 relative overflow-hidden">

          {/* Background Image */}
          <div className="absolute inset-0 z-0">
            <Image 
              src="/hexagonal-bg.jpg" 
              alt="Background" 
              fill
              className="object-cover"
            />
          </div>
          
          {/* Content Container */}
          <div className="relative z-10 flex flex-col items-center gap-8 w-full">
      
            {/* Dashboard */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/dashboard-icon.svg" alt="Dashboard" width={40} height={40} />
              <span className="text-[10px] text-gray-800 text-center">Dashboard</span>
            </div>

            {/* Live Monitoring */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/monitoring-icon.svg" alt="Live Monitoring" width={40} height={40} />
              <span className="text-[10px] text-gray-800 text-center">Live Monitoring</span>
            </div>

            {/* Search */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/search-icon.svg" alt="Search" width={40} height={40} />
              <span className="text-[10px] text-gray-800 text-center">Search</span>
            </div>

            {/* Admin Console */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/admin-icon.svg" alt="Admin Console" width={40} height={40} />
              <span className="text-[10px] text-gray-800 text-center">Admin Console</span>
            </div>

            {/* About */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/about-icon.svg" alt="About" width={40} height={40} />
              <span className="text-[10px] text-gray-800 text-center">About</span>
            </div>

          </div>
          
        </div>
    )
}