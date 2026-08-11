/// <reference types="vite/client" />
import { POIResponse } from '../services/api';

export interface Attraction {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number;
    price?: string;
    rating: number;
    tags: string[];
    location: string;
    duration: string;
    type: 'landmark' | 'museum' | 'nature' | 'cultural' | 'adventure';
}

export interface Restaurant {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number;
    price: string;
    rating: number;
    cuisine: string[];
    location: string;
    type: 'fine-dining' | 'casual' | 'cafe' | 'street-food' | 'bistro';
    specialty: string;
}

export interface Activity {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number; // 1-100
    price: string;
    rating: number;
    duration: string;
    groupSize: string;
    difficulty: 'Easy' | 'Moderate' | 'Challenging';
    type: 'outdoor' | 'cultural' | 'adventure' | 'tour' | 'workshop';
    location: string;
    includes: string[];
}

// --- Randomized Descriptions ---
const genericDescriptions = {
    attraction: [
        "A must-visit destination capturing the essence of the city.",
        "Immerse yourself in the local culture and history here.",
        "A breathtaking spot perfect for photography and relaxation.",
        "Experience the vibrant atmosphere and unique charm.",
        "A hidden gem that offers a unique perspective of the area.",
        "Discover the rich heritage and stories behind this landmark.",
        "An unforgettable experience for nature and adventure lovers.",
        "Perfect for a leisurely exploration of local traditions.",
        "A chaotic yet mesmerizing blend of sights and sounds.",
        "Step back in time and marvel at the architectural beauty."
    ],
    restaurant: [
        "Savor the authentic flavors of local cuisine.",
        "A delightful culinary journey awaits you here.",
        "Perfect for a memorable meal with friends and family.",
        "Experience the perfect blend of taste and ambiance.",
        "A gastronomic delight showcasing the best local ingredients.",
        "Indulge in a feast for the senses at this top-rated spot.",
        "Where traditional recipes meet modern culinary art.",
        "Enjoy a vibrant dining atmosphere with exquisite dishes.",
        "A taste of heaven for food enthusiasts.",
        "Culinary excellence served with warm hospitality."
    ],
    accommodation: [
        "Experience world-class comfort and hospitality.",
        "A cozy retreat in the heart of the city.",
        "Luxury living with stunning views and amenities.",
        "Modern elegance meets traditional charm.",
        "Your perfect home away from home with premium services.",
        "Relax and rejuvenate in this tranquil urban oasis.",
        "Stylish accommodations designed for the modern traveler.",
        "Enjoy a stay defined by elegance and exceptional service.",
        "A sophisticated sanctuary amidst the city buzz.",
        "Unwind in style with top-notch facilities and comfort."
    ],
    activity: [
        "An exciting local activity to enjoy.",
        "Create lasting memories with this unique experience.",
        "Perfect for adventure seekers and culture lovers.",
        "Engage with the local community and traditions.",
        "A fun-filled experience for all ages."
    ],
    shopping: [
        "Discover unique treasures and local crafts.",
        "A shopper's paradise with endless variety.",
        "Explore the best local markets and boutiques.",
        "Find the perfect souvenir to take home.",
        "Experience the vibrant shopping culture.",
        "From luxury brands to local finds, it's all here.",
        "A delightful mix of traditional and modern shopping.",
        "Uncover hidden gems in this bustling market.",
        "Shop 'til you drop in this vibrant district.",
        "A must-visit for fashion and lifestyle enthusiasts."
    ],
    wellness: [
        "Rejuvenate your mind, body, and soul.",
        "A tranquil escape from the city's hustle.",
        "Experience ultimate relaxation and pampering.",
        "Restore your balance in this peaceful sanctuary.",
        "Indulge in world-class wellness treatments.",
        "A perfect spot for meditation and reflection.",
        "Revitalize yourself with holistic therapies.",
        "Find your inner peace in this serene setting.",
        "A haven of tranquility and well-being.",
        "Escape to a world of calm and comfort."
    ],
    entertainment: [
        "Experience the vibrant nightlife and entertainment.",
        "A perfect evening of fun and excitement.",
        "Enjoy world-class performances and shows.",
        "Immerse yourself in the local arts scene.",
        "A lively atmosphere that keeps you entertained.",
        "Dance the night away at this popular spot.",
        "Witness captivating cultural performances.",
        "An unforgettable night out with friends.",
        "The heart of the city's entertainment district.",
        "Enjoy a memorable evening of music and fun."
    ]
};

export const getRandomDescription = (type: keyof typeof genericDescriptions) => {
    const options = genericDescriptions[type];
    return options[Math.floor(Math.random() * options.length)];
};

export function mapPOIToAttraction(poi: any): Attraction {
    // Helper to determine type from categories
    const determineType = (categories: string[] = []): Attraction['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('museum'))) return 'museum';
        if (cats.some(c => c.includes('park') || c.includes('nature'))) return 'nature';
        if (cats.some(c => c.includes('temple') || c.includes('church') || c.includes('culture'))) return 'cultural';
        if (cats.some(c => c.includes('adventure') || c.includes('hiking'))) return 'adventure';
        return 'landmark';
    };

    // Helper to format price with randomization
    const formatPrice = (level?: number) => {
        if (!level) return 'Free';
        const base = level * 500;
        const randomOffset = Math.floor(Math.random() * 200);
        const min = base + randomOffset;
        const max = base + 500 + randomOffset;
        return `₹${min}-${max}`;
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('attraction'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&h=600&fit=crop'), // Fallback
        suggested: Math.round(poi.ai_score || 80),
        price: formatPrice(poi.price_level),
        rating: poi.rating || 4.5,
        tags: poi.category || ['Attraction'],
        location: poi.formatted_address || '',
        duration: '2-3 hours', // Default estimate
        type: determineType(poi.category)
    };
}

export function mapPOIToRestaurant(poi: any): Restaurant {
    const formatPrice = (level?: number) => {
        const base = (level || 1) * 400;
        const randomOffset = Math.floor(Math.random() * 150);
        return `₹${base + randomOffset}-${base + 400 + randomOffset}`;
    };

    const determineType = (categories: string[] = []): Restaurant['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('cafe') || c.includes('coffee'))) return 'cafe';
        if (cats.some(c => c.includes('fine dining'))) return 'fine-dining';
        if (cats.some(c => c.includes('street'))) return 'street-food';
        if (cats.some(c => c.includes('bistro'))) return 'bistro';
        return 'casual';
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('restaurant'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        price: formatPrice(poi.price_level),
        rating: poi.rating || 4.5,
        cuisine: poi.category ? poi.category.slice(0, 2) : ['Local'],
        location: poi.formatted_address || '',
        type: determineType(poi.category),
        specialty: 'Local Specialties'
    };
}

export function mapPOIToActivity(poi: any): Activity {
    const determineType = (categories: string[] = []): Activity['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('museum') || c.includes('culture'))) return 'cultural';
        if (cats.some(c => c.includes('adventure') || c.includes('hiking'))) return 'adventure';
        if (cats.some(c => c.includes('workshop'))) return 'workshop';
        if (cats.some(c => c.includes('tour'))) return 'tour';
        return 'outdoor';
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('activity'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        price: '₹500-1500', // Placeholder as POI might not have activity price
        rating: poi.rating || 4.5,
        duration: '2-3 hours',
        groupSize: 'Variable',
        difficulty: 'Moderate',
        type: determineType(poi.category),
        location: poi.formatted_address || '',
        includes: ['Entry', 'Guide']
    };
}

export interface Accommodation {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number; // 1-100
    price: string;
    rating: number;
    amenities: string[];
    location: string;
    type: 'hotel' | 'hostel' | 'airbnb' | 'resort' | 'boutique';
    rooms: string;
    guests: number;
}

export function mapPOIToAccommodation(poi: any): Accommodation {
    const determineType = (categories: string[] = []): Accommodation['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('resort'))) return 'resort';
        if (cats.some(c => c.includes('hostel'))) return 'hostel';
        if (cats.some(c => c.includes('guest house') || c.includes('bnb'))) return 'airbnb';
        if (cats.some(c => c.includes('boutique'))) return 'boutique';
        return 'hotel';
    };

    const formatPrice = (level?: number) => {
        const base = (level || 2) * 2000;
        const randomOffset = Math.floor(Math.random() * 1000);
        return `₹${base + randomOffset}-${base + 3000 + randomOffset}/night`;
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('accommodation'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        price: formatPrice(poi.price_level),
        rating: poi.rating || 4.5,
        amenities: ['Wi-Fi', 'AC', 'Restaurant'], // Default amenities as POI might not have them
        location: poi.formatted_address || '',
        type: determineType(poi.category),
        rooms: 'Standard Room',
        guests: 2
    };
}

export interface Entertainment {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number; // 1-100
    price: string;
    rating: number;
    location: string;
    type: 'theater' | 'concert' | 'cabaret' | 'nightclub' | 'bar' | 'cultural';
    schedule: string;
    atmosphere: string;
    features: string[];
    dressCode?: string;
}

export function mapPOIToEntertainment(poi: any): Entertainment {
    const determineType = (categories: string[] = []): Entertainment['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('night_club') || c.includes('club'))) return 'nightclub';
        if (cats.some(c => c.includes('bar') || c.includes('pub'))) return 'bar';
        if (cats.some(c => c.includes('theater') || c.includes('theatre'))) return 'theater';
        if (cats.some(c => c.includes('concert') || c.includes('music'))) return 'concert';
        if (cats.some(c => c.includes('art') || c.includes('culture'))) return 'cultural';
        return 'cultural';
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('entertainment'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        price: '₹1000-3000',
        rating: poi.rating || 4.5,
        location: poi.formatted_address || '',
        type: determineType(poi.category),
        schedule: 'Open late',
        atmosphere: 'Vibrant',
        features: ['Live Entertainment', 'Drinks'],
        dressCode: 'Smart Casual'
    };
}

export interface ShoppingDestination {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number; // 1-100
    priceRange: string;
    rating: number;
    location: string;
    type: 'luxury' | 'markets' | 'boutiques' | 'department' | 'vintage' | 'souvenirs';
    specialties: string[];
    hours: string;
    atmosphere: string;
}

export function mapPOIToShopping(poi: any): ShoppingDestination {
    const determineType = (categories: string[] = []): ShoppingDestination['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('department_store') || c.includes('shopping_mall'))) return 'department';
        if (cats.some(c => c.includes('clothing_store') || c.includes('boutique'))) return 'boutiques';
        if (cats.some(c => c.includes('jewelry') || c.includes('watch'))) return 'luxury';
        if (cats.some(c => c.includes('market') || c.includes('bazaar'))) return 'markets';
        if (cats.some(c => c.includes('antique') || c.includes('vintage'))) return 'vintage';
        if (cats.some(c => c.includes('gift') || c.includes('souvenir'))) return 'souvenirs';
        return 'boutiques';
    };

    const formatPrice = (level?: number) => {
        if (!level) return '₹₹';
        if (level === 1) return '₹';
        if (level === 2) return '₹₹';
        if (level === 3) return '₹₹₹';
        return '₹₹₹₹';
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('shopping'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        priceRange: formatPrice(poi.price_level),
        rating: poi.rating || 4.5,
        location: poi.formatted_address || '',
        type: determineType(poi.category),
        specialties: ['Fashion', 'Accessories'],
        hours: '10:00 - 21:00',
        atmosphere: 'Bustling'
    };
}

export interface WellnessLocation {
    id: string;
    name: string;
    description: string;
    image: string;
    suggested: number; // 1-100
    price: string;
    rating: number;
    location: string;
    type: 'spa' | 'park' | 'garden' | 'beach' | 'thermal' | 'yoga';
    duration: string;
    features: string[];
    atmosphere: string;
    bestTime: string;
}

export function mapPOIToWellness(poi: any): WellnessLocation {
    const determineType = (categories: string[] = []): WellnessLocation['type'] => {
        const cats = categories.map(c => c.toLowerCase());
        if (cats.some(c => c.includes('spa'))) return 'spa';
        if (cats.some(c => c.includes('park'))) return 'park';
        if (cats.some(c => c.includes('garden'))) return 'garden';
        if (cats.some(c => c.includes('beach'))) return 'beach';
        if (cats.some(c => c.includes('gym') || c.includes('fitness'))) return 'yoga';
        return 'park';
    };

    return {
        id: poi.place_id,
        name: poi.name,
        description: poi.why_recommended || poi.editorial_summary || getRandomDescription('wellness'),
        image: poi.photo_url || (poi.photo_reference
            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${poi.photo_reference}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`
            : 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=800&h=600&fit=crop'),
        suggested: Math.round(poi.ai_score || 80),
        price: '₹500-2000',
        rating: poi.rating || 4.5,
        location: poi.formatted_address || '',
        type: determineType(poi.category),
        duration: '1-2 hours',
        features: ['Relaxation', 'Wellness'],
        atmosphere: 'Peaceful',
        bestTime: 'Morning'
    };
}
