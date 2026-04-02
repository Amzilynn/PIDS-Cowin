import { motion } from 'framer-motion';

export const springTransition = { type: "spring", stiffness: 300, damping: 30 };
export const pageVariants = {
  initial: { opacity: 0, y: 15, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -15, scale: 0.99 }
};

export const Card = ({ children, className = "" }) => (
  <motion.div 
    whileHover={{ y: -5, boxShadow: "0 20px 40px rgba(0,0,0,0.04)" }}
    transition={springTransition}
    className={`bg-white border border-slate-200 rounded-[24px] p-6 shadow-sm ${className}`}
  >
    {children}
  </motion.div>
);
