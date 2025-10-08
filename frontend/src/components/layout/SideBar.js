import Image from "next/image";
  
export default function Sidebar(){ 
    return( 
        <div className="hidden md:flex w-[8%] flex-col items-center py-25 gap-8 border-r border-black ">
      
            {/* Dashboard */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/dashboard-icon.svg" alt="Dashboard" width={32} height={32} />
              <span className="text-[10px] text-gray-800 text-center">Dashboard</span>
            </div>

            {/* Live Monitoring */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/monitoring-icon.svg" alt="Live Monitoring" width={32} height={32} />
              <span className="text-[10px] text-gray-800 text-center">Live Monitoring</span>
            </div>

            {/* Search */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/search-icon.svg" alt="Search" width={32} height={32} />
              <span className="text-[10px] text-gray-800 text-center">Search</span>
            </div>

            {/* Admin Console */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/admin-icon.svg" alt="Admin Console" width={32} height={32} />
              <span className="text-[10px] text-gray-800 text-center">Admin Console</span>
            </div>

            {/* About */}
            <div className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-70 transition-opacity">
              <Image src="/icons/about-icon.svg" alt="About" width={32} height={32} />
              <span className="text-[10px] text-gray-800 text-center">About</span>
            </div>
          
        </div>
    )
}