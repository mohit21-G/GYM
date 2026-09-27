import { PrismaClient, Role, UserStatus, Gender, ActivityLevel } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  console.log('--- Starting Database Seeding ---');

  // 1. Seed Food Categories
  const foodCategories = [
    { name: 'Breads & Grains', description: 'Rotis, rice, bread, oats, and grains', icon: 'wheat' },
    { name: 'Pulses & Lentils', description: 'Dals, legumes, chickpeas, and beans', icon: 'bean' },
    { name: 'Dairy & Alternatives', description: 'Milk, curd, paneer, tofu, yogurt', icon: 'milk' },
    { name: 'Proteins & Meats', description: 'Eggs, chicken, fish, whey protein', icon: 'egg' },
    { name: 'Vegetables & Sabzi', description: 'Cooked vegetables, raw salads, greens', icon: 'carrot' },
    { name: 'Fruits & Berries', description: 'Fresh fruits, dried fruits, smoothies', icon: 'apple' },
    { name: 'Snacks & Light Meals', description: 'Khakhra, roasted makhana, nuts, poha', icon: 'cookie' },
    { name: 'Beverages & Drinks', description: 'Water, green tea, chaas, coconut water', icon: 'cup-soda' },
  ];

  const categoryMap = new Map<string, string>();
  for (const cat of foodCategories) {
    const record = await prisma.foodCategory.upsert({
      where: { name: cat.name },
      update: { description: cat.description, icon: cat.icon },
      create: cat,
    });
    categoryMap.set(cat.name, record.id);
  }
  console.log(`Seeded ${foodCategories.length} food categories.`);

  // 2. Seed Common Foods with Nutritional Data & Synonyms
  const foods = [
    // Breads & Grains
    {
      category: 'Breads & Grains',
      name: 'Khapli Wheat Rotli',
      standardServingSize: 1,
      standardServingUnit: 'piece',
      caloriesPerServing: 85,
      proteinG: 3.5,
      carbsG: 16.5,
      fatG: 0.8,
      fiberG: 3.2,
      sodiumMg: 15,
      synonyms: 'khapli rotli, emmer wheat roti, khapli chapati, rotli',
    },
    {
      category: 'Breads & Grains',
      name: 'Whole Wheat Roti',
      standardServingSize: 1,
      standardServingUnit: 'piece',
      caloriesPerServing: 90,
      proteinG: 3.0,
      carbsG: 18.0,
      fatG: 1.0,
      fiberG: 2.5,
      sodiumMg: 20,
      synonyms: 'roti, chapati, fulka, phulka, rotli',
    },
    {
      category: 'Breads & Grains',
      name: 'Cooked White Rice',
      standardServingSize: 150,
      standardServingUnit: 'g',
      caloriesPerServing: 195,
      proteinG: 4.0,
      carbsG: 43.0,
      fatG: 0.5,
      fiberG: 0.6,
      sodiumMg: 5,
      synonyms: 'rice, bhat, chawal, cooked rice',
    },
    {
      category: 'Breads & Grains',
      name: 'Cooked Brown Rice',
      standardServingSize: 150,
      standardServingUnit: 'g',
      caloriesPerServing: 168,
      proteinG: 3.8,
      carbsG: 35.0,
      fatG: 1.4,
      fiberG: 2.8,
      sodiumMg: 5,
      synonyms: 'brown rice, brown bhat',
    },
    {
      category: 'Breads & Grains',
      name: 'Rolled Oats (Cooked)',
      standardServingSize: 200,
      standardServingUnit: 'g',
      caloriesPerServing: 140,
      proteinG: 5.0,
      carbsG: 24.0,
      fatG: 2.5,
      fiberG: 4.0,
      sodiumMg: 10,
      synonyms: 'oatmeal, oats, porridge',
    },

    // Pulses & Lentils
    {
      category: 'Pulses & Lentils',
      name: 'Toor Dal Tadka',
      standardServingSize: 150,
      standardServingUnit: 'g',
      caloriesPerServing: 145,
      proteinG: 7.5,
      carbsG: 20.0,
      fatG: 4.0,
      fiberG: 4.5,
      sodiumMg: 220,
      synonyms: 'dal, toor dal, dal fry, khati mithi dal, gujarati dal',
    },
    {
      category: 'Pulses & Lentils',
      name: 'Moong Dal Khichdi',
      standardServingSize: 200,
      standardServingUnit: 'g',
      caloriesPerServing: 220,
      proteinG: 8.0,
      carbsG: 38.0,
      fatG: 4.5,
      fiberG: 5.0,
      sodiumMg: 280,
      synonyms: 'khichdi, moong dal khichdi, khichdi kadhi',
    },
    {
      category: 'Pulses & Lentils',
      name: 'Boiled Chana / Chickpeas',
      standardServingSize: 100,
      standardServingUnit: 'g',
      caloriesPerServing: 164,
      proteinG: 8.9,
      carbsG: 27.4,
      fatG: 2.6,
      fiberG: 7.6,
      sodiumMg: 24,
      synonyms: 'chana, chickpeas, kabuli chana, kala chana',
    },

    // Dairy
    {
      category: 'Dairy & Alternatives',
      name: 'Paneer (Raw / Cubes)',
      standardServingSize: 100,
      standardServingUnit: 'g',
      caloriesPerServing: 265,
      proteinG: 18.3,
      carbsG: 3.4,
      fatG: 20.8,
      fiberG: 0,
      sodiumMg: 22,
      synonyms: 'cottage cheese, paneer, fresh paneer',
    },
    {
      category: 'Dairy & Alternatives',
      name: 'Plain Greek Yogurt / Curd',
      standardServingSize: 150,
      standardServingUnit: 'g',
      caloriesPerServing: 90,
      proteinG: 15.0,
      carbsG: 5.5,
      fatG: 0.5,
      fiberG: 0,
      sodiumMg: 50,
      synonyms: 'curd, dahi, yogurt, greek yogurt',
    },
    {
      category: 'Dairy & Alternatives',
      name: 'Cow Milk (Toned)',
      standardServingSize: 250,
      standardServingUnit: 'ml',
      caloriesPerServing: 145,
      proteinG: 8.0,
      carbsG: 12.0,
      fatG: 7.5,
      fiberG: 0,
      sodiumMg: 110,
      synonyms: 'milk, doodh, cow milk',
    },

    // Proteins & Meats
    {
      category: 'Proteins & Meats',
      name: 'Boiled Whole Egg',
      standardServingSize: 1,
      standardServingUnit: 'piece',
      caloriesPerServing: 78,
      proteinG: 6.3,
      carbsG: 0.6,
      fatG: 5.3,
      fiberG: 0,
      sodiumMg: 62,
      synonyms: 'boiled egg, egg, anda, whole egg',
    },
    {
      category: 'Proteins & Meats',
      name: 'Egg White (Boiled)',
      standardServingSize: 1,
      standardServingUnit: 'piece',
      caloriesPerServing: 17,
      proteinG: 3.6,
      carbsG: 0.2,
      fatG: 0.1,
      fiberG: 0,
      sodiumMg: 55,
      synonyms: 'egg white, boiled egg white, ando',
    },
    {
      category: 'Proteins & Meats',
      name: 'Grilled Chicken Breast',
      standardServingSize: 100,
      standardServingUnit: 'g',
      caloriesPerServing: 165,
      proteinG: 31.0,
      carbsG: 0,
      fatG: 3.6,
      fiberG: 0,
      sodiumMg: 74,
      synonyms: 'chicken breast, chicken, grilled chicken',
    },
    {
      category: 'Proteins & Meats',
      name: 'Whey Protein Isolate',
      standardServingSize: 1,
      standardServingUnit: 'scoop',
      caloriesPerServing: 120,
      proteinG: 25.0,
      carbsG: 2.0,
      fatG: 1.0,
      fiberG: 0,
      sodiumMg: 140,
      synonyms: 'whey, protein shake, protein powder, whey scoop',
    },

    // Fruits
    {
      category: 'Fruits & Berries',
      name: 'Apple',
      standardServingSize: 1,
      standardServingUnit: 'medium',
      caloriesPerServing: 95,
      proteinG: 0.5,
      carbsG: 25.0,
      fatG: 0.3,
      fiberG: 4.4,
      sodiumMg: 2,
      synonyms: 'apple, safarjan, seb',
    },
    {
      category: 'Fruits & Berries',
      name: 'Banana',
      standardServingSize: 1,
      standardServingUnit: 'medium',
      caloriesPerServing: 105,
      proteinG: 1.3,
      carbsG: 27.0,
      fatG: 0.3,
      fiberG: 3.1,
      sodiumMg: 1,
      synonyms: 'banana, kela, keda',
    },

    // Beverages
    {
      category: 'Beverages & Drinks',
      name: 'Masala Chai (with Milk & Sugar)',
      standardServingSize: 150,
      standardServingUnit: 'ml',
      caloriesPerServing: 90,
      proteinG: 2.5,
      carbsG: 14.0,
      fatG: 2.5,
      fiberG: 0,
      sodiumMg: 35,
      synonyms: 'chai, tea, masala tea, cha',
    },
    {
      category: 'Beverages & Drinks',
      name: 'Fresh Coconut Water',
      standardServingSize: 250,
      standardServingUnit: 'ml',
      caloriesPerServing: 45,
      proteinG: 1.0,
      carbsG: 9.0,
      fatG: 0.5,
      fiberG: 2.5,
      sodiumMg: 60,
      synonyms: 'coconut water, nariyal pani, nariyal paani',
    },
  ];

  for (const food of foods) {
    const categoryId = categoryMap.get(food.category);
    if (!categoryId) continue;

    await prisma.food.upsert({
      where: { id: `seed-food-${food.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}` },
      update: {
        categoryId,
        name: food.name,
        standardServingSize: food.standardServingSize,
        standardServingUnit: food.standardServingUnit,
        caloriesPerServing: food.caloriesPerServing,
        proteinG: food.proteinG,
        carbsG: food.carbsG,
        fatG: food.fatG,
        fiberG: food.fiberG,
        sodiumMg: food.sodiumMg,
        synonyms: food.synonyms,
      },
      create: {
        id: `seed-food-${food.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
        categoryId,
        name: food.name,
        standardServingSize: food.standardServingSize,
        standardServingUnit: food.standardServingUnit,
        caloriesPerServing: food.caloriesPerServing,
        proteinG: food.proteinG,
        carbsG: food.carbsG,
        fatG: food.fatG,
        fiberG: food.fiberG,
        sodiumMg: food.sodiumMg,
        synonyms: food.synonyms,
      },
    });
  }
  console.log(`Seeded ${foods.length} common food records.`);

  // 3. Seed Activity Categories
  const activityCategories = [
    { name: 'Cardio & Aerobics', description: 'Walking, running, cycling, rowing', icon: 'footprints' },
    { name: 'Strength & Conditioning', description: 'Gym weights, bodyweight exercises, crossfit', icon: 'dumbbell' },
    { name: 'Sports & Games', description: 'Badminton, cricket, football, tennis', icon: 'trophy' },
    { name: 'Flexibility & Mind-Body', description: 'Yoga, pilates, stretching, mobility', icon: 'heart-pulse' },
    { name: 'Daily Physical Activities', description: 'Cleaning, gardening, stairs climbing', icon: 'home' },
  ];

  const actCatMap = new Map<string, string>();
  for (const cat of activityCategories) {
    const record = await prisma.activityCategory.upsert({
      where: { name: cat.name },
      update: { description: cat.description, icon: cat.icon },
      create: cat,
    });
    actCatMap.set(cat.name, record.id);
  }
  console.log(`Seeded ${activityCategories.length} activity categories.`);

  // 4. Seed Common Activities with MET values
  const activities = [
    {
      category: 'Cardio & Aerobics',
      name: 'Moderate Walking (4 km/h)',
      metValue: 3.5,
      description: 'Casual or leisurely walking at a moderate pace',
      synonyms: 'walk, walking, chaalvu, pagpala',
    },
    {
      category: 'Cardio & Aerobics',
      name: 'Brisk Walking (5.5 km/h)',
      metValue: 4.5,
      description: 'Fast paced energetic walking',
      synonyms: 'brisk walk, fast walking, speed walking',
    },
    {
      category: 'Cardio & Aerobics',
      name: 'Outdoor Running / Jogging',
      metValue: 8.0,
      description: 'Continuous running at roughly 8 km/h',
      synonyms: 'running, jog, jogging, dodvu',
    },
    {
      category: 'Cardio & Aerobics',
      name: 'Outdoor / Stationary Cycling',
      metValue: 6.0,
      description: 'Moderate effort bicycling',
      synonyms: 'cycling, cycle, bike, biking',
    },
    {
      category: 'Cardio & Aerobics',
      name: 'Swimming (Freestyle)',
      metValue: 7.0,
      description: 'Lap swimming at moderate effort',
      synonyms: 'swimming, swim, tarvu',
    },
    {
      category: 'Strength & Conditioning',
      name: 'Gym Strength Training',
      metValue: 5.0,
      description: 'Resistance training with weights or machines',
      synonyms: 'gym, strength training, weight lifting, workout, weights, kasrat',
    },
    {
      category: 'Strength & Conditioning',
      name: 'High Intensity Interval Training (HIIT)',
      metValue: 8.5,
      description: 'Intense bodyweight and cardiovascular circuits',
      synonyms: 'hiit, interval training, circuit training',
    },
    {
      category: 'Flexibility & Mind-Body',
      name: 'Hatha / Vinyasa Yoga',
      metValue: 3.0,
      description: 'Yoga asanas, breathing, and stretching',
      synonyms: 'yoga, pranayama, asana, surya namaskar',
    },
    {
      category: 'Sports & Games',
      name: 'Badminton',
      metValue: 5.5,
      description: 'Competitive or recreational badminton singles/doubles',
      synonyms: 'badminton, shuttle',
    },
    {
      category: 'Sports & Games',
      name: 'Cricket',
      metValue: 4.8,
      description: 'Batting, bowling, and fielding practice/match',
      synonyms: 'cricket, match',
    },
  ];

  for (const act of activities) {
    const categoryId = actCatMap.get(act.category);
    if (!categoryId) continue;

    await prisma.activity.upsert({
      where: { id: `seed-act-${act.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}` },
      update: {
        categoryId,
        name: act.name,
        metValue: act.metValue,
        description: act.description,
        synonyms: act.synonyms,
      },
      create: {
        id: `seed-act-${act.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
        categoryId,
        name: act.name,
        metValue: act.metValue,
        description: act.description,
        synonyms: act.synonyms,
      },
    });
  }
  console.log(`Seeded ${activities.length} activity records.`);

  // 5. Seed Default Admin User from Environment Variables ONLY
  const adminEmail = process.env.ADMIN_EMAIL || 'admin@fitbit-ai.com';
  const adminRawPassword = process.env.ADMIN_PASSWORD || 'Admin@123456';
  const adminName = process.env.ADMIN_NAME || 'System Administrator';

  const passwordHash = await bcrypt.hash(adminRawPassword, 10);

  const admin = await prisma.user.upsert({
    where: { email: adminEmail },
    update: {
      name: adminName,
      role: Role.ADMIN,
      status: UserStatus.ACTIVE,
    },
    create: {
      name: adminName,
      username: 'admin',
      email: adminEmail,
      passwordHash,
      role: Role.ADMIN,
      status: UserStatus.ACTIVE,
      profile: {
        create: {
          gender: Gender.OTHER,
          activityLevel: ActivityLevel.MODERATE,
        },
      },
    },
  });

  console.log(`Seeded Default Admin User: ${admin.email} (Role: ${admin.role})`);
  console.log('--- Database Seeding Completed Successfully ---');
}

main()
  .catch((e) => {
    console.error('Database seeding failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
