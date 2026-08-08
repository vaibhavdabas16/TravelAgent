
# Warp Product Manual

## Project Overview

This project is a modern, AI-powered trip planner that allows users to create personalized travel itineraries based on their preferences. Built with a sophisticated tech stack, the application provides a seamless, intuitive, and visually appealing experience for planning and viewing trip details.

### Key Features

- **AI-Driven Planning Flow**: A multi-step process that guides users through planning their trip, including defining the destination, dates, group size, and travel style.
- **Dynamic Itinerary Generation**: Based on user input, the application generates a detailed, day-by-day itinerary with curated recommendations for activities, dining, and accommodations.
- **Interactive Trip Plan**: The generated trip plan is displayed in a well-structured and engaging format, featuring maps, images, and budget information.
- **Component-Based Architecture**: The application is built with a modular, reusable component-based architecture, ensuring maintainability and scalability.

## Technical Deep-Dive

### Core Components and Files

- **`main.tsx`**: The entry point of the application, responsible for rendering the main `App` component.
- **`App.tsx`**: The central component that manages the application's view state (e.g., home, planning, trip plan) and handles the data flow between different sections.
- **`package.json`**: Defines the project's dependencies and scripts. Key dependencies include **React**, **TypeScript**, **Vite**, **Radix UI**, **Tailwind CSS**, and **Framer Motion**.
- **`vite.config.ts`**: The Vite configuration file, which defines the build settings, server options, and aliases for streamlined development.
- **`src/components/`**: This directory contains all the React components that make up the application's UI.
  - **`planning-flow.tsx`**: Manages the multi-step trip planning process, guiding users through each stage of creating their itinerary.
  - **`trip-plan.tsx`**: Displays the final generated trip plan in a detailed, interactive, and visually rich format.
  - **`hero-section.tsx`**: The main landing page component, which serves as the entry point for users to start planning their trip.
  - **`navbar.tsx`**: The navigation bar, providing consistent branding and access to key application features.
  - **`planning-sections/*`**: A collection of specialized components for each step of the planning process, such as `places-to-visit.tsx`, `accommodations.tsx`, and `dining.tsx`.

### Data Flow

1. **Initiation**: The user begins on the **`HeroSection`**, where they can start the trip planning process.
2. **State Transition**: The `App` component transitions its state to `planning`, which renders the **`PlanningFlow`** component.
3. **User Input**: The user progresses through the guided steps in the **`PlanningFlow`**, making selections for their destination, travel dates, and preferences for activities, dining, and lodging.
4. **Data Aggregation**: The **`PlanningFlow`** component collects and manages the user's selections in its state.
5. **Completion and Data Transfer**: Upon completing the planning flow, the `onComplete` callback is triggered, passing the aggregated planning data to the `App` component.
6. **Final Itinerary**: The `App` component updates its state to `trip-plan` and renders the **`TripPlan`** component, which receives the planning data as props.
7. **Display**: The **`TripPlan`** component uses the received data to generate and display a comprehensive, day-by-day itinerary, complete with mock data fallbacks to ensure a robust user experience.

This documentation provides a complete overview of the project's structure, functionality, and data flow, enabling a thorough understanding of its technical implementation.
