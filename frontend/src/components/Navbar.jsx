import { NavLink } from 'react-router-dom'

function Navbar({ user, onLogout }) {
  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <span className="text-xl font-semibold text-gray-800">
          Study Tool
        </span>
        <div className="flex items-center gap-6">
          <NavLink
            to="/upload"
            className={({ isActive }) =>
              isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-800"
            }
          >
            Upload
          </NavLink>
          <NavLink
            to="/flashcards"
            className={({ isActive }) =>
              isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-800"
            }
          >
            Flashcards
          </NavLink>
          <NavLink
            to="/chat"
            className={({ isActive }) =>
              isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-800"
            }
          >
            Chat
          </NavLink>
          <NavLink
            to="/quiz"
            className={({ isActive }) =>
              isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-800"
            }
          >
            Quiz
          </NavLink>
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-gray-200">
            <span className="text-gray-600 text-sm">{user?.name}</span>
            <button
              onClick={onLogout}
              className="text-gray-400 hover:text-gray-600 text-sm transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar